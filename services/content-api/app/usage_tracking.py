"""
API usage tracking and cost management
"""
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
from app.logging_config import app_logger
from app.caching import cache_manager
from app.config import settings

class UsageTracker:
    """Track API usage and costs"""
    
    def __init__(self):
        self.usage_data = defaultdict(lambda: {
            "requests": 0,
            "tokens": 0,
            "cost": 0.0,
            "errors": 0
        })
        
        # Cost configuration (per 1000 tokens)
        self.cost_per_1k_tokens = {
            "gpt-4-turbo-preview": 0.01,  # Input tokens
            "gpt-4-turbo-preview-output": 0.03,  # Output tokens
            "gpt-3.5-turbo": 0.0005,
            "gpt-3.5-turbo-output": 0.0015,
        }
        
        # Usage limits per API key
        self.limits = {
            "daily_requests": 1000,
            "daily_tokens": 1000000,
            "daily_cost_usd": 50.0,
            "monthly_requests": 30000,
            "monthly_tokens": 30000000,
            "monthly_cost_usd": 1000.0
        }
        
        # Track usage by time period
        self.hourly_usage = defaultdict(lambda: defaultdict(int))
        self.daily_usage = defaultdict(lambda: defaultdict(int))
        self.monthly_usage = defaultdict(lambda: defaultdict(int))
    
    async def track_request(
        self,
        api_key: str,
        service: str,
        endpoint: str,
        tokens_used: int = 0,
        cost: float = 0.0,
        success: bool = True
    ):
        """Track an API request"""
        now = datetime.utcnow()
        hour_key = now.strftime("%Y-%m-%d-%H")
        day_key = now.strftime("%Y-%m-%d")
        month_key = now.strftime("%Y-%m")
        
        # Update in-memory tracking
        self.usage_data[api_key]["requests"] += 1
        self.usage_data[api_key]["tokens"] += tokens_used
        self.usage_data[api_key]["cost"] += cost
        if not success:
            self.usage_data[api_key]["errors"] += 1
        
        # Track by time period
        self.hourly_usage[api_key][hour_key] += 1
        self.daily_usage[api_key][day_key] += 1
        self.monthly_usage[api_key][month_key] += 1
        
        # Store in Redis for persistence
        await self._store_usage_redis(api_key, service, endpoint, tokens_used, cost)
        
        # Log usage
        app_logger.log_business_metric(
            "api_usage",
            tokens_used,
            api_key=api_key[:8] + "...",  # Partial key for security
            service=service,
            endpoint=endpoint,
            cost=cost,
            success=success
        )
    
    async def _store_usage_redis(
        self,
        api_key: str,
        service: str,
        endpoint: str,
        tokens: int,
        cost: float
    ):
        """Store usage data in Redis"""
        if not cache_manager.redis_client:
            return
        
        try:
            now = datetime.utcnow()
            day_key = f"usage:daily:{api_key}:{now.strftime('%Y-%m-%d')}"
            month_key = f"usage:monthly:{api_key}:{now.strftime('%Y-%m')}"
            
            # Increment counters
            pipeline = cache_manager.redis_client.pipeline()
            
            # Daily usage
            pipeline.hincrby(day_key, "requests", 1)
            pipeline.hincrby(day_key, "tokens", tokens)
            pipeline.hincrbyfloat(day_key, "cost", cost)
            pipeline.expire(day_key, 86400 * 7)  # Keep for 7 days
            
            # Monthly usage
            pipeline.hincrby(month_key, "requests", 1)
            pipeline.hincrby(month_key, "tokens", tokens)
            pipeline.hincrbyfloat(month_key, "cost", cost)
            pipeline.expire(month_key, 86400 * 35)  # Keep for 35 days
            
            # Service-specific tracking
            service_key = f"usage:service:{service}:{now.strftime('%Y-%m-%d')}"
            pipeline.hincrby(service_key, endpoint, 1)
            pipeline.expire(service_key, 86400 * 7)
            
            await pipeline.execute()
            
        except Exception as e:
            app_logger.log_error("usage_redis_store_error", str(e))
    
    async def check_limits(
        self,
        api_key: str,
        tokens_requested: int = 0
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if usage is within limits
        Returns: (is_allowed, limit_info)
        """
        now = datetime.utcnow()
        day_key = now.strftime("%Y-%m-%d")
        month_key = now.strftime("%Y-%m")
        
        # Get current usage from Redis
        daily_usage = await self._get_usage_from_redis(api_key, "daily", day_key)
        monthly_usage = await self._get_usage_from_redis(api_key, "monthly", month_key)
        
        # Check daily limits
        daily_checks = {
            "requests": daily_usage.get("requests", 0) < self.limits["daily_requests"],
            "tokens": daily_usage.get("tokens", 0) + tokens_requested < self.limits["daily_tokens"],
            "cost": daily_usage.get("cost", 0) < self.limits["daily_cost_usd"]
        }
        
        # Check monthly limits
        monthly_checks = {
            "requests": monthly_usage.get("requests", 0) < self.limits["monthly_requests"],
            "tokens": monthly_usage.get("tokens", 0) + tokens_requested < self.limits["monthly_tokens"],
            "cost": monthly_usage.get("cost", 0) < self.limits["monthly_cost_usd"]
        }
        
        is_allowed = all(daily_checks.values()) and all(monthly_checks.values())
        
        limit_info = {
            "allowed": is_allowed,
            "daily": {
                "requests_used": daily_usage.get("requests", 0),
                "requests_limit": self.limits["daily_requests"],
                "tokens_used": daily_usage.get("tokens", 0),
                "tokens_limit": self.limits["daily_tokens"],
                "cost_used": daily_usage.get("cost", 0),
                "cost_limit": self.limits["daily_cost_usd"]
            },
            "monthly": {
                "requests_used": monthly_usage.get("requests", 0),
                "requests_limit": self.limits["monthly_requests"],
                "tokens_used": monthly_usage.get("tokens", 0),
                "tokens_limit": self.limits["monthly_tokens"],
                "cost_used": monthly_usage.get("cost", 0),
                "cost_limit": self.limits["monthly_cost_usd"]
            },
            "exceeded": []
        }
        
        # Identify what limits were exceeded
        if not daily_checks["requests"]:
            limit_info["exceeded"].append("daily_requests")
        if not daily_checks["tokens"]:
            limit_info["exceeded"].append("daily_tokens")
        if not daily_checks["cost"]:
            limit_info["exceeded"].append("daily_cost")
        if not monthly_checks["requests"]:
            limit_info["exceeded"].append("monthly_requests")
        if not monthly_checks["tokens"]:
            limit_info["exceeded"].append("monthly_tokens")
        if not monthly_checks["cost"]:
            limit_info["exceeded"].append("monthly_cost")
        
        if not is_allowed:
            app_logger.logger.warning(
                "usage_limit_exceeded",
                api_key=api_key[:8] + "...",
                exceeded=limit_info["exceeded"]
            )
        
        return is_allowed, limit_info
    
    async def _get_usage_from_redis(
        self,
        api_key: str,
        period: str,
        period_key: str
    ) -> Dict[str, Any]:
        """Get usage data from Redis"""
        if not cache_manager.redis_client:
            return {}
        
        try:
            key = f"usage:{period}:{api_key}:{period_key}"
            data = await cache_manager.redis_client.hgetall(key)
            
            return {
                "requests": int(data.get("requests", 0)),
                "tokens": int(data.get("tokens", 0)),
                "cost": float(data.get("cost", 0))
            }
        except Exception as e:
            app_logger.log_error("usage_redis_get_error", str(e))
            return {}
    
    def calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Calculate cost based on token usage"""
        input_cost = self.cost_per_1k_tokens.get(model, 0.01) * (input_tokens / 1000)
        output_cost = self.cost_per_1k_tokens.get(f"{model}-output", 0.03) * (output_tokens / 1000)
        return input_cost + output_cost
    
    async def get_usage_report(
        self,
        api_key: str,
        period: str = "daily"
    ) -> Dict[str, Any]:
        """Get usage report for an API key"""
        now = datetime.utcnow()
        
        if period == "daily":
            period_key = now.strftime("%Y-%m-%d")
        elif period == "weekly":
            # Get last 7 days
            usage_data = {}
            for i in range(7):
                day = now - timedelta(days=i)
                day_key = day.strftime("%Y-%m-%d")
                daily_data = await self._get_usage_from_redis(api_key, "daily", day_key)
                if daily_data:
                    usage_data[day_key] = daily_data
            
            return {
                "period": "weekly",
                "api_key": api_key[:8] + "...",
                "data": usage_data,
                "total": {
                    "requests": sum(d.get("requests", 0) for d in usage_data.values()),
                    "tokens": sum(d.get("tokens", 0) for d in usage_data.values()),
                    "cost": sum(d.get("cost", 0) for d in usage_data.values())
                }
            }
        elif period == "monthly":
            period_key = now.strftime("%Y-%m")
        else:
            period_key = now.strftime("%Y-%m-%d")
        
        usage = await self._get_usage_from_redis(api_key, period, period_key)
        
        return {
            "period": period,
            "period_key": period_key,
            "api_key": api_key[:8] + "...",
            "usage": usage,
            "limits": self.limits,
            "remaining": {
                "requests": self.limits[f"{period}_requests"] - usage.get("requests", 0),
                "tokens": self.limits[f"{period}_tokens"] - usage.get("tokens", 0),
                "cost": self.limits[f"{period}_cost_usd"] - usage.get("cost", 0)
            }
        }
    
    async def get_service_analytics(
        self,
        service: str,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get analytics for a specific service"""
        if not date:
            date = datetime.utcnow().strftime("%Y-%m-%d")
        
        if not cache_manager.redis_client:
            return {}
        
        try:
            key = f"usage:service:{service}:{date}"
            data = await cache_manager.redis_client.hgetall(key)
            
            return {
                "service": service,
                "date": date,
                "endpoints": data,
                "total_requests": sum(int(v) for v in data.values())
            }
        except Exception as e:
            app_logger.log_error("service_analytics_error", str(e))
            return {}
    
    def set_custom_limits(
        self,
        api_key: str,
        limits: Dict[str, Any]
    ):
        """Set custom limits for a specific API key"""
        # Store custom limits (in production, save to database)
        custom_key = f"limits:{api_key}"
        # This would be stored in database or Redis
        app_logger.logger.info(
            "custom_limits_set",
            api_key=api_key[:8] + "...",
            limits=limits
        )

# Global usage tracker
usage_tracker = UsageTracker()

# Middleware for automatic usage tracking
from fastapi import Request
from typing import Tuple

async def track_usage_middleware(request: Request, call_next):
    """Middleware to track API usage"""
    # Extract API key from request
    api_key = request.headers.get("X-API-Key", "anonymous")
    
    # Track request
    await usage_tracker.track_request(
        api_key=api_key,
        service="content_api",
        endpoint=request.url.path,
        success=True  # Will be updated based on response
    )
    
    response = await call_next(request)
    return response

class CostEstimator:
    """Estimate costs for content generation"""
    
    @staticmethod
    def estimate_content_cost(
        platforms: List[str],
        content_length: str = "medium"
    ) -> Dict[str, float]:
        """Estimate cost for content generation"""
        # Rough token estimates
        token_estimates = {
            "short": 500,
            "medium": 1000,
            "long": 2000
        }
        
        base_tokens = token_estimates.get(content_length, 1000)
        tokens_per_platform = base_tokens * len(platforms)
        
        # Assume GPT-4 turbo
        cost = usage_tracker.calculate_cost(
            "gpt-4-turbo-preview",
            input_tokens=tokens_per_platform // 2,
            output_tokens=tokens_per_platform // 2
        )
        
        return {
            "estimated_tokens": tokens_per_platform,
            "estimated_cost_usd": round(cost, 4),
            "platforms": len(platforms),
            "content_length": content_length
        }

cost_estimator = CostEstimator()