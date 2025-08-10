"""
Reliable webhook handling with retries and dead letter queue
"""
import httpx
import asyncio
import hashlib
import hmac
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from app.logging_config import app_logger
from app.error_handling import WEBHOOK_RETRY
from app.config import settings
import json

class WebhookHandler:
    """Handles webhook delivery with reliability features"""
    
    def __init__(self):
        self.pending_webhooks: List[Dict[str, Any]] = []
        self.failed_webhooks: List[Dict[str, Any]] = []
        self.webhook_secret = settings.api_key  # Use API key as webhook secret
        self.max_retries = 3
        self.retry_delays = [5, 30, 120]  # Seconds between retries
    
    def _generate_signature(self, payload: str) -> str:
        """Generate HMAC signature for webhook payload"""
        signature = hmac.new(
            self.webhook_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"
    
    def _verify_signature(self, payload: str, signature: str) -> bool:
        """Verify webhook signature"""
        expected = self._generate_signature(payload)
        return hmac.compare_digest(expected, signature)
    
    @WEBHOOK_RETRY
    async def _send_webhook(
        self,
        url: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None
    ) -> httpx.Response:
        """Send webhook with retry logic"""
        async with httpx.AsyncClient(timeout=30) as client:
            payload_str = json.dumps(payload)
            signature = self._generate_signature(payload_str)
            
            request_headers = {
                "Content-Type": "application/json",
                "X-Webhook-Signature": signature,
                "X-Webhook-Timestamp": str(int(datetime.utcnow().timestamp()))
            }
            
            if headers:
                request_headers.update(headers)
            
            response = await client.post(
                url,
                json=payload,
                headers=request_headers
            )
            response.raise_for_status()
            return response
    
    async def send_webhook(
        self,
        url: str,
        event_type: str,
        data: Dict[str, Any],
        campaign_id: Optional[str] = None,
        retry_on_failure: bool = True
    ) -> Dict[str, Any]:
        """
        Send webhook with automatic retry and queuing
        """
        webhook_id = hashlib.md5(
            f"{url}{event_type}{datetime.utcnow()}".encode()
        ).hexdigest()[:12]
        
        payload = {
            "webhook_id": webhook_id,
            "event_type": event_type,
            "campaign_id": campaign_id,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        app_logger.logger.info(
            "webhook_sending",
            webhook_id=webhook_id,
            url=url,
            event_type=event_type
        )
        
        try:
            response = await self._send_webhook(url, payload)
            
            app_logger.logger.info(
                "webhook_delivered",
                webhook_id=webhook_id,
                status_code=response.status_code
            )
            
            return {
                "webhook_id": webhook_id,
                "status": "delivered",
                "status_code": response.status_code,
                "delivered_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            app_logger.log_error(
                "webhook_delivery_failed",
                str(e),
                webhook_id=webhook_id,
                url=url
            )
            
            if retry_on_failure:
                # Add to retry queue
                await self._queue_for_retry(url, payload, webhook_id)
            
            return {
                "webhook_id": webhook_id,
                "status": "failed",
                "error": str(e),
                "queued_for_retry": retry_on_failure
            }
    
    async def _queue_for_retry(
        self,
        url: str,
        payload: Dict[str, Any],
        webhook_id: str,
        attempt: int = 0
    ):
        """Queue failed webhook for retry"""
        retry_data = {
            "webhook_id": webhook_id,
            "url": url,
            "payload": payload,
            "attempt": attempt,
            "next_retry": datetime.utcnow() + timedelta(seconds=self.retry_delays[min(attempt, 2)]),
            "created_at": datetime.utcnow()
        }
        
        self.pending_webhooks.append(retry_data)
        
        app_logger.logger.info(
            "webhook_queued_for_retry",
            webhook_id=webhook_id,
            attempt=attempt,
            next_retry=retry_data["next_retry"].isoformat()
        )
    
    async def process_retry_queue(self):
        """Process webhooks in retry queue"""
        now = datetime.utcnow()
        to_process = []
        
        # Find webhooks ready for retry
        for webhook in self.pending_webhooks:
            if webhook["next_retry"] <= now:
                to_process.append(webhook)
        
        for webhook in to_process:
            self.pending_webhooks.remove(webhook)
            
            if webhook["attempt"] >= self.max_retries:
                # Move to dead letter queue
                self.failed_webhooks.append({
                    **webhook,
                    "failed_at": now,
                    "failure_reason": "max_retries_exceeded"
                })
                
                app_logger.logger.error(
                    "webhook_moved_to_dlq",
                    webhook_id=webhook["webhook_id"],
                    attempts=webhook["attempt"]
                )
                continue
            
            # Attempt retry
            try:
                response = await self._send_webhook(
                    webhook["url"],
                    webhook["payload"]
                )
                
                app_logger.logger.info(
                    "webhook_retry_succeeded",
                    webhook_id=webhook["webhook_id"],
                    attempt=webhook["attempt"] + 1
                )
                
            except Exception as e:
                # Queue for another retry
                await self._queue_for_retry(
                    webhook["url"],
                    webhook["payload"],
                    webhook["webhook_id"],
                    webhook["attempt"] + 1
                )
    
    async def get_webhook_status(self, webhook_id: str) -> Dict[str, Any]:
        """Get status of a webhook"""
        # Check pending queue
        for webhook in self.pending_webhooks:
            if webhook["webhook_id"] == webhook_id:
                return {
                    "webhook_id": webhook_id,
                    "status": "pending_retry",
                    "attempt": webhook["attempt"],
                    "next_retry": webhook["next_retry"].isoformat()
                }
        
        # Check failed queue
        for webhook in self.failed_webhooks:
            if webhook["webhook_id"] == webhook_id:
                return {
                    "webhook_id": webhook_id,
                    "status": "failed",
                    "attempts": webhook["attempt"],
                    "failed_at": webhook["failed_at"].isoformat(),
                    "reason": webhook.get("failure_reason", "unknown")
                }
        
        return {
            "webhook_id": webhook_id,
            "status": "unknown"
        }
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get webhook queue statistics"""
        return {
            "pending_count": len(self.pending_webhooks),
            "failed_count": len(self.failed_webhooks),
            "oldest_pending": min(
                (w["created_at"] for w in self.pending_webhooks),
                default=None
            ),
            "retry_queue": [
                {
                    "webhook_id": w["webhook_id"],
                    "attempt": w["attempt"],
                    "next_retry": w["next_retry"].isoformat()
                }
                for w in self.pending_webhooks[:5]  # Show first 5
            ]
        }

# Global webhook handler
webhook_handler = WebhookHandler()

# Background task for processing retry queue
async def webhook_retry_processor():
    """Background task to process webhook retry queue"""
    while True:
        try:
            await webhook_handler.process_retry_queue()
        except Exception as e:
            app_logger.log_error("webhook_retry_processor_error", str(e))
        
        await asyncio.sleep(30)  # Check every 30 seconds

class WebhookReceiver:
    """Handle incoming webhooks from n8n and other services"""
    
    def __init__(self):
        self.webhook_handlers: Dict[str, Callable] = {}
        self.received_webhooks: List[Dict[str, Any]] = []
    
    def register_handler(self, event_type: str, handler: Callable):
        """Register a handler for a specific webhook event type"""
        self.webhook_handlers[event_type] = handler
        app_logger.logger.info("webhook_handler_registered", event_type=event_type)
    
    async def process_webhook(
        self,
        event_type: str,
        data: Dict[str, Any],
        signature: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process incoming webhook"""
        webhook_id = hashlib.md5(
            f"{event_type}{datetime.utcnow()}".encode()
        ).hexdigest()[:12]
        
        # Verify signature if provided
        if signature and settings.environment == "production":
            payload_str = json.dumps(data)
            if not webhook_handler._verify_signature(payload_str, signature):
                app_logger.log_security_event(
                    "invalid_webhook_signature",
                    event_type=event_type
                )
                return {
                    "webhook_id": webhook_id,
                    "status": "rejected",
                    "reason": "invalid_signature"
                }
        
        # Store webhook for audit
        self.received_webhooks.append({
            "webhook_id": webhook_id,
            "event_type": event_type,
            "data": data,
            "received_at": datetime.utcnow()
        })
        
        # Trim history to last 1000 webhooks
        if len(self.received_webhooks) > 1000:
            self.received_webhooks = self.received_webhooks[-1000:]
        
        # Process webhook with registered handler
        if event_type in self.webhook_handlers:
            try:
                handler = self.webhook_handlers[event_type]
                result = await handler(data)
                
                app_logger.logger.info(
                    "webhook_processed",
                    webhook_id=webhook_id,
                    event_type=event_type
                )
                
                return {
                    "webhook_id": webhook_id,
                    "status": "processed",
                    "result": result
                }
                
            except Exception as e:
                app_logger.log_error(
                    "webhook_processing_error",
                    str(e),
                    webhook_id=webhook_id,
                    event_type=event_type
                )
                
                return {
                    "webhook_id": webhook_id,
                    "status": "error",
                    "error": str(e)
                }
        else:
            app_logger.logger.warning(
                "unhandled_webhook_event",
                event_type=event_type,
                webhook_id=webhook_id
            )
            
            return {
                "webhook_id": webhook_id,
                "status": "unhandled",
                "event_type": event_type
            }
    
    def get_webhook_history(
        self,
        event_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get webhook reception history"""
        webhooks = self.received_webhooks
        
        if event_type:
            webhooks = [w for w in webhooks if w["event_type"] == event_type]
        
        return sorted(
            webhooks,
            key=lambda w: w["received_at"],
            reverse=True
        )[:limit]

# Global webhook receiver
webhook_receiver = WebhookReceiver()

# Register default handlers
async def handle_content_approved(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle content approval webhook"""
    campaign_id = data.get("campaign_id")
    app_logger.log_business_metric(
        "content_approved",
        1,
        campaign_id=campaign_id
    )
    # Trigger publishing workflow
    return {"action": "publish", "campaign_id": campaign_id}

async def handle_performance_update(data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle performance update webhook"""
    content_id = data.get("content_id")
    metrics = data.get("metrics", {})
    app_logger.log_business_metric(
        "performance_updated",
        1,
        content_id=content_id,
        **metrics
    )
    return {"action": "metrics_stored", "content_id": content_id}

# Register default handlers
webhook_receiver.register_handler("content_approved", handle_content_approved)
webhook_receiver.register_handler("performance_update", handle_performance_update)