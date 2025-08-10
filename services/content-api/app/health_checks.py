"""
Enhanced health checks for production monitoring
"""
import httpx
import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta
import time
from app.config import settings
from app.logging_config import app_logger
from app.database import check_database_health
from app.caching import cache_manager

class HealthChecker:
    """Comprehensive health checking system"""
    
    def __init__(self):
        self.last_check_time = None
        self.check_cache = {}
        self.cache_ttl = 30  # Cache health results for 30 seconds
    
    async def check_all_health(self) -> Dict[str, Any]:
        """Run all health checks"""
        now = datetime.utcnow()
        
        # Use cached results if recent
        if (
            self.last_check_time and 
            (now - self.last_check_time).total_seconds() < self.cache_ttl and
            self.check_cache
        ):
            return self.check_cache
        
        start_time = time.time()
        
        # Run all checks concurrently
        checks = await asyncio.gather(
            self.check_database(),
            self.check_redis(),
            self.check_openai(),
            self.check_external_apis(),
            self.check_disk_space(),
            self.check_memory(),
            self.check_webhooks(),
            return_exceptions=True
        )
        
        check_time = time.time() - start_time
        
        # Process results
        health_results = {
            "status": "healthy",
            "timestamp": now.isoformat(),
            "check_duration_seconds": round(check_time, 2),
            "checks": {
                "database": self._process_check_result(checks[0]),
                "redis": self._process_check_result(checks[1]),
                "openai": self._process_check_result(checks[2]),
                "external_apis": self._process_check_result(checks[3]),
                "disk_space": self._process_check_result(checks[4]),
                "memory": self._process_check_result(checks[5]),
                "webhooks": self._process_check_result(checks[6])
            },
            "summary": {
                "total_checks": len(checks),
                "healthy_checks": 0,
                "unhealthy_checks": 0,
                "warning_checks": 0
            }
        }
        
        # Calculate overall health status
        overall_healthy = True
        for check_name, check_result in health_results["checks"].items():
            if isinstance(check_result, dict):
                if check_result.get("status") == "healthy":
                    health_results["summary"]["healthy_checks"] += 1
                elif check_result.get("status") == "warning":
                    health_results["summary"]["warning_checks"] += 1
                    if overall_healthy:
                        health_results["status"] = "warning"
                else:
                    health_results["summary"]["unhealthy_checks"] += 1
                    health_results["status"] = "unhealthy"
                    overall_healthy = False
        
        # Cache results
        self.check_cache = health_results
        self.last_check_time = now
        
        # Log overall health
        app_logger.logger.info(
            "health_check_completed",
            status=health_results["status"],
            duration=check_time,
            healthy_checks=health_results["summary"]["healthy_checks"],
            unhealthy_checks=health_results["summary"]["unhealthy_checks"]
        )
        
        return health_results
    
    def _process_check_result(self, result) -> Dict[str, Any]:
        """Process individual check result"""
        if isinstance(result, Exception):
            return {
                "status": "error",
                "healthy": False,
                "error": str(result)
            }
        return result
    
    async def check_database(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            start_time = time.time()
            db_health = await check_database_health()
            response_time = time.time() - start_time
            
            return {
                "status": "healthy" if db_health.get("healthy") else "unhealthy",
                "healthy": db_health.get("healthy", False),
                "response_time_seconds": round(response_time, 3),
                "pool_status": db_health.get("pool_status", {}),
                "details": db_health
            }
        except Exception as e:
            app_logger.log_error("database_health_check_error", str(e))
            return {
                "status": "error",
                "healthy": False,
                "error": str(e)
            }
    
    async def check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity and performance"""
        if not cache_manager.redis_client:
            return {
                "status": "warning",
                "healthy": False,
                "message": "Redis not configured"
            }
        
        try:
            start_time = time.time()
            
            # Test basic operations
            test_key = "health_check_test"
            await cache_manager.redis_client.set(test_key, "test_value", ex=60)
            value = await cache_manager.redis_client.get(test_key)
            await cache_manager.redis_client.delete(test_key)
            
            response_time = time.time() - start_time
            
            # Get Redis info
            info = await cache_manager.redis_client.info()
            
            return {
                "status": "healthy",
                "healthy": True,
                "response_time_seconds": round(response_time, 3),
                "memory_usage_mb": round(info.get("used_memory", 0) / 1024 / 1024, 2),
                "connected_clients": info.get("connected_clients", 0),
                "cache_stats": cache_manager.get_stats()
            }
        except Exception as e:
            app_logger.log_error("redis_health_check_error", str(e))
            return {
                "status": "unhealthy",
                "healthy": False,
                "error": str(e)
            }
    
    async def check_openai(self) -> Dict[str, Any]:
        """Check OpenAI API connectivity"""
        if not settings.openai_api_key:
            return {
                "status": "warning",
                "healthy": False,
                "message": "OpenAI API key not configured"
            }
        
        try:
            start_time = time.time()
            
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {settings.openai_api_key}"}
                )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "healthy": True,
                    "response_time_seconds": round(response_time, 3),
                    "api_status": "accessible"
                }
            else:
                return {
                    "status": "warning",
                    "healthy": False,
                    "status_code": response.status_code,
                    "message": "OpenAI API returned error"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "healthy": False,
                "error": str(e)
            }
    
    async def check_external_apis(self) -> Dict[str, Any]:
        """Check external API services"""
        apis_to_check = []
        
        # Add configured APIs
        if settings.meta_access_token:
            apis_to_check.append(("Meta Graph API", "https://graph.facebook.com/me"))
        if settings.linkedin_access_token:
            apis_to_check.append(("LinkedIn API", "https://api.linkedin.com/v2/me"))
        
        if not apis_to_check:
            return {
                "status": "warning",
                "healthy": True,
                "message": "No external APIs configured"
            }
        
        results = {}
        overall_healthy = True
        
        for api_name, api_url in apis_to_check:
            try:
                start_time = time.time()
                async with httpx.AsyncClient(timeout=5) as client:
                    # Just check if the endpoint is reachable (don't send auth)
                    response = await client.get(api_url.split('/me')[0])  # Just check base URL
                response_time = time.time() - start_time
                
                results[api_name] = {
                    "healthy": response.status_code < 500,
                    "response_time_seconds": round(response_time, 3),
                    "status_code": response.status_code
                }
                
                if response.status_code >= 500:
                    overall_healthy = False
                    
            except Exception as e:
                results[api_name] = {
                    "healthy": False,
                    "error": str(e)
                }
                overall_healthy = False
        
        return {
            "status": "healthy" if overall_healthy else "warning",
            "healthy": overall_healthy,
            "apis": results
        }
    
    async def check_disk_space(self) -> Dict[str, Any]:
        """Check disk space usage"""
        try:
            import shutil
            
            total, used, free = shutil.disk_usage("/")
            used_percent = (used / total) * 100
            
            status = "healthy"
            if used_percent > 90:
                status = "unhealthy"
            elif used_percent > 80:
                status = "warning"
            
            return {
                "status": status,
                "healthy": used_percent < 90,
                "used_percent": round(used_percent, 1),
                "free_gb": round(free / 1024**3, 1),
                "total_gb": round(total / 1024**3, 1)
            }
        except Exception as e:
            return {
                "status": "error",
                "healthy": False,
                "error": str(e)
            }
    
    async def check_memory(self) -> Dict[str, Any]:
        """Check memory usage"""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            
            status = "healthy"
            if memory.percent > 90:
                status = "unhealthy"
            elif memory.percent > 80:
                status = "warning"
            
            return {
                "status": status,
                "healthy": memory.percent < 90,
                "used_percent": round(memory.percent, 1),
                "available_mb": round(memory.available / 1024**2, 1),
                "total_mb": round(memory.total / 1024**2, 1)
            }
        except Exception as e:
            return {
                "status": "error",
                "healthy": False,
                "error": str(e)
            }
    
    async def check_webhooks(self) -> Dict[str, Any]:
        """Check webhook system health"""
        try:
            from app.webhook_handler import webhook_handler
            
            stats = webhook_handler.get_queue_stats()
            
            status = "healthy"
            if stats["failed_count"] > 100:
                status = "unhealthy"
            elif stats["failed_count"] > 10:
                status = "warning"
            
            return {
                "status": status,
                "healthy": stats["failed_count"] < 100,
                "pending_webhooks": stats["pending_count"],
                "failed_webhooks": stats["failed_count"],
                "oldest_pending": stats.get("oldest_pending")
            }
        except Exception as e:
            return {
                "status": "error",
                "healthy": False,
                "error": str(e)
            }
    
    async def check_service_dependencies(self) -> Dict[str, Any]:
        """Check critical service dependencies"""
        dependencies = []
        
        # Check n8n connectivity
        if hasattr(settings, 'n8n_host'):
            dependencies.append({
                "name": "n8n",
                "url": f"https://{settings.n8n_host}",
                "critical": True
            })
        
        results = {}
        for dep in dependencies:
            try:
                async with httpx.AsyncClient(timeout=5) as client:
                    response = await client.get(dep["url"])
                results[dep["name"]] = {
                    "healthy": response.status_code < 500,
                    "status_code": response.status_code,
                    "critical": dep["critical"]
                }
            except Exception as e:
                results[dep["name"]] = {
                    "healthy": False,
                    "error": str(e),
                    "critical": dep["critical"]
                }
        
        return results
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get cached health summary"""
        if not self.check_cache:
            return {"status": "unknown", "message": "No health checks run yet"}
        
        return {
            "status": self.check_cache.get("status", "unknown"),
            "last_check": self.check_cache.get("timestamp"),
            "summary": self.check_cache.get("summary", {}),
            "age_seconds": (
                (datetime.utcnow() - self.last_check_time).total_seconds()
                if self.last_check_time else None
            )
        }

# Global health checker
health_checker = HealthChecker()

# Background task for periodic health checks
async def periodic_health_check():
    """Background task to perform periodic health checks"""
    while True:
        try:
            health_result = await health_checker.check_all_health()
            
            # Log if unhealthy
            if health_result["status"] != "healthy":
                app_logger.logger.warning(
                    "system_health_degraded",
                    status=health_result["status"],
                    unhealthy_checks=health_result["summary"]["unhealthy_checks"]
                )
            
        except Exception as e:
            app_logger.log_error("periodic_health_check_error", str(e))
        
        # Wait 5 minutes between checks
        await asyncio.sleep(300)