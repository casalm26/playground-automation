"""
Production-grade error handling with retry logic and circuit breakers
"""
from typing import Any, Callable, Optional, Dict
from functools import wraps
import asyncio
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
import structlog
from datetime import datetime, timedelta
import httpx
from fastapi import HTTPException

logger = structlog.get_logger()

# Circuit breaker state storage
circuit_breakers: Dict[str, Dict] = {}

class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is open"""
    pass

class CircuitBreaker:
    """Simple circuit breaker implementation"""
    
    def __init__(self, name: str, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
        
    def call_succeeded(self):
        """Reset the circuit breaker on success"""
        self.failure_count = 0
        self.state = "closed"
        logger.info("circuit_breaker_reset", name=self.name)
        
    def call_failed(self):
        """Record a failure and potentially open the circuit"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(
                "circuit_breaker_opened",
                name=self.name,
                failure_count=self.failure_count
            )
            
    def is_open(self) -> bool:
        """Check if circuit breaker should block calls"""
        if self.state == "closed":
            return False
            
        if self.state == "open":
            # Check if recovery timeout has passed
            if self.last_failure_time:
                time_since_failure = (datetime.utcnow() - self.last_failure_time).total_seconds()
                if time_since_failure > self.recovery_timeout:
                    self.state = "half-open"
                    logger.info("circuit_breaker_half_open", name=self.name)
                    return False
            return True
            
        return False

def circuit_breaker(name: str, failure_threshold: int = 5, recovery_timeout: int = 60):
    """Decorator to add circuit breaker to async functions"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get or create circuit breaker
            if name not in circuit_breakers:
                circuit_breakers[name] = CircuitBreaker(name, failure_threshold, recovery_timeout)
            
            breaker = circuit_breakers[name]
            
            if breaker.is_open():
                logger.warning("circuit_breaker_blocked", name=name)
                raise CircuitBreakerOpen(f"Circuit breaker {name} is open")
            
            try:
                result = await func(*args, **kwargs)
                breaker.call_succeeded()
                return result
            except Exception as e:
                breaker.call_failed()
                raise e
                
        return wrapper
    return decorator

# Retry configurations for different services
OPENAI_RETRY = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((httpx.HTTPError, TimeoutError)),
    before_sleep=before_sleep_log(logger, structlog.INFO)
)

PLATFORM_API_RETRY = retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    retry=retry_if_exception_type((httpx.HTTPError, ConnectionError)),
    before_sleep=before_sleep_log(logger, structlog.INFO)
)

WEBHOOK_RETRY = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(httpx.HTTPError),
    before_sleep=before_sleep_log(logger, structlog.INFO)
)

class ErrorHandler:
    """Centralized error handling"""
    
    @staticmethod
    def handle_api_error(error: Exception, service: str) -> Dict[str, Any]:
        """Handle external API errors consistently"""
        logger.error(
            "external_api_error",
            service=service,
            error_type=type(error).__name__,
            error_message=str(error)
        )
        
        if isinstance(error, httpx.HTTPStatusError):
            if error.response.status_code == 429:
                return {
                    "error": "Rate limit exceeded",
                    "service": service,
                    "retry_after": error.response.headers.get("Retry-After", 60)
                }
            elif error.response.status_code >= 500:
                return {
                    "error": "Service temporarily unavailable",
                    "service": service,
                    "status_code": error.response.status_code
                }
        
        return {
            "error": "External service error",
            "service": service,
            "details": str(error)
        }
    
    @staticmethod
    def handle_validation_error(error: Exception, context: str) -> Dict[str, Any]:
        """Handle input validation errors"""
        logger.warning(
            "validation_error",
            context=context,
            error_message=str(error)
        )
        
        return {
            "error": "Validation failed",
            "context": context,
            "details": str(error)
        }
    
    @staticmethod
    def handle_content_error(error: Exception, content_type: str) -> Dict[str, Any]:
        """Handle content generation errors"""
        logger.error(
            "content_generation_error",
            content_type=content_type,
            error_message=str(error)
        )
        
        return {
            "error": "Content generation failed",
            "content_type": content_type,
            "fallback": "Please try again with different parameters"
        }

class WebhookQueue:
    """Dead letter queue for failed webhooks"""
    
    def __init__(self):
        self.failed_webhooks = []
        self.max_queue_size = 1000
    
    async def add_failed_webhook(self, webhook_data: Dict[str, Any]):
        """Add failed webhook to queue for retry"""
        if len(self.failed_webhooks) >= self.max_queue_size:
            # Remove oldest webhook
            self.failed_webhooks.pop(0)
        
        self.failed_webhooks.append({
            "data": webhook_data,
            "failed_at": datetime.utcnow(),
            "retry_count": webhook_data.get("retry_count", 0) + 1
        })
        
        logger.warning(
            "webhook_added_to_dlq",
            webhook_url=webhook_data.get("url"),
            retry_count=webhook_data.get("retry_count", 0)
        )
    
    async def process_failed_webhooks(self):
        """Process webhooks in the dead letter queue"""
        processed = []
        
        for webhook in self.failed_webhooks:
            if webhook["retry_count"] < 5:
                # Try to resend
                try:
                    await self._resend_webhook(webhook["data"])
                    processed.append(webhook)
                    logger.info(
                        "webhook_retry_succeeded",
                        webhook_url=webhook["data"].get("url")
                    )
                except Exception as e:
                    logger.error(
                        "webhook_retry_failed",
                        webhook_url=webhook["data"].get("url"),
                        error=str(e)
                    )
        
        # Remove successfully processed webhooks
        for webhook in processed:
            self.failed_webhooks.remove(webhook)
    
    async def _resend_webhook(self, webhook_data: Dict[str, Any]):
        """Attempt to resend a webhook"""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                webhook_data["url"],
                json=webhook_data["payload"],
                headers=webhook_data.get("headers", {})
            )
            response.raise_for_status()

# Global webhook queue instance
webhook_queue = WebhookQueue()

async def safe_api_call(
    func: Callable,
    *args,
    service_name: str,
    fallback_value: Optional[Any] = None,
    **kwargs
) -> Any:
    """Safely call an external API with error handling"""
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        error_data = ErrorHandler.handle_api_error(e, service_name)
        
        if fallback_value is not None:
            logger.warning(
                "using_fallback_value",
                service=service_name,
                error=str(e)
            )
            return fallback_value
        
        raise HTTPException(
            status_code=503,
            detail=error_data
        )

# Background task to process failed webhooks
async def webhook_retry_task():
    """Background task to retry failed webhooks"""
    while True:
        try:
            await webhook_queue.process_failed_webhooks()
        except Exception as e:
            logger.error("webhook_retry_task_error", error=str(e))
        
        await asyncio.sleep(300)  # Run every 5 minutes