from fastapi import Request, Response
from typing import Dict, Any
import time
import psutil
import os
from datetime import datetime
from app.config import settings

# Metrics storage (in production, use proper metrics backend)
metrics_store: Dict[str, Any] = {
    "requests": {
        "total": 0,
        "by_endpoint": {},
        "by_status": {},
        "response_times": []
    },
    "system": {
        "cpu_percent": 0,
        "memory_percent": 0,
        "disk_usage": 0
    },
    "api_calls": {
        "openai": {"total": 0, "errors": 0, "avg_response_time": 0},
        "meta": {"total": 0, "errors": 0, "avg_response_time": 0},
        "linkedin": {"total": 0, "errors": 0, "avg_response_time": 0}
    },
    "content_generation": {
        "total_campaigns": 0,
        "successful_campaigns": 0,
        "failed_campaigns": 0,
        "avg_generation_time": 0
    }
}

class MetricsCollector:
    """Collects and stores application metrics"""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
    
    def record_request(self, method: str, path: str, status_code: int, response_time: float):
        """Record HTTP request metrics"""
        metrics_store["requests"]["total"] += 1
        
        # Track by endpoint
        endpoint_key = f"{method} {path}"
        if endpoint_key not in metrics_store["requests"]["by_endpoint"]:
            metrics_store["requests"]["by_endpoint"][endpoint_key] = 0
        metrics_store["requests"]["by_endpoint"][endpoint_key] += 1
        
        # Track by status code
        if status_code not in metrics_store["requests"]["by_status"]:
            metrics_store["requests"]["by_status"][status_code] = 0
        metrics_store["requests"]["by_status"][status_code] += 1
        
        # Track response times (keep last 1000)
        metrics_store["requests"]["response_times"].append(response_time)
        if len(metrics_store["requests"]["response_times"]) > 1000:
            metrics_store["requests"]["response_times"].pop(0)
    
    def record_api_call(self, provider: str, success: bool, response_time: float):
        """Record external API call metrics"""
        if provider in metrics_store["api_calls"]:
            metrics_store["api_calls"][provider]["total"] += 1
            if not success:
                metrics_store["api_calls"][provider]["errors"] += 1
            
            # Update average response time
            current_avg = metrics_store["api_calls"][provider]["avg_response_time"]
            total_calls = metrics_store["api_calls"][provider]["total"]
            new_avg = ((current_avg * (total_calls - 1)) + response_time) / total_calls
            metrics_store["api_calls"][provider]["avg_response_time"] = new_avg
    
    def record_content_generation(self, success: bool, generation_time: float):
        """Record content generation metrics"""
        metrics_store["content_generation"]["total_campaigns"] += 1
        if success:
            metrics_store["content_generation"]["successful_campaigns"] += 1
        else:
            metrics_store["content_generation"]["failed_campaigns"] += 1
        
        # Update average generation time
        total = metrics_store["content_generation"]["total_campaigns"]
        current_avg = metrics_store["content_generation"]["avg_generation_time"]
        new_avg = ((current_avg * (total - 1)) + generation_time) / total
        metrics_store["content_generation"]["avg_generation_time"] = new_avg
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            metrics_store["system"] = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_mb": memory.used // (1024 * 1024),
                "memory_total_mb": memory.total // (1024 * 1024),
                "disk_usage_percent": (disk.used / disk.total) * 100,
                "disk_free_gb": disk.free // (1024 * 1024 * 1024)
            }
        except Exception as e:
            print(f"Error collecting system metrics: {e}")
        
        return metrics_store["system"]
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status"""
        system_metrics = self.get_system_metrics()
        
        health_status = "healthy"
        issues = []
        
        # Check system resources
        if system_metrics["cpu_percent"] > 80:
            health_status = "warning"
            issues.append("High CPU usage")
        
        if system_metrics["memory_percent"] > 85:
            health_status = "warning"
            issues.append("High memory usage")
        
        if system_metrics.get("disk_usage_percent", 0) > 90:
            health_status = "critical"
            issues.append("Low disk space")
        
        # Check API error rates
        for provider, stats in metrics_store["api_calls"].items():
            if stats["total"] > 0:
                error_rate = stats["errors"] / stats["total"]
                if error_rate > 0.1:  # 10% error rate
                    health_status = "warning" if health_status == "healthy" else health_status
                    issues.append(f"High {provider} API error rate: {error_rate:.2%}")
        
        # Check content generation success rate
        content_stats = metrics_store["content_generation"]
        if content_stats["total_campaigns"] > 0:
            success_rate = content_stats["successful_campaigns"] / content_stats["total_campaigns"]
            if success_rate < 0.9:  # Less than 90% success rate
                health_status = "warning" if health_status == "healthy" else health_status
                issues.append(f"Low content generation success rate: {success_rate:.2%}")
        
        return {
            "status": health_status,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "issues": issues,
            "system": system_metrics,
            "version": "1.0.0",
            "environment": settings.environment
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics"""
        # Calculate derived metrics
        response_times = metrics_store["requests"]["response_times"]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)]
        else:
            avg_response_time = 0
            p95_response_time = 0
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "requests": {
                **metrics_store["requests"],
                "avg_response_time": avg_response_time,
                "p95_response_time": p95_response_time
            },
            "system": self.get_system_metrics(),
            "api_calls": metrics_store["api_calls"],
            "content_generation": metrics_store["content_generation"]
        }

# Global metrics collector
metrics_collector = MetricsCollector()

async def metrics_middleware(request: Request, call_next):
    """Middleware to collect request metrics"""
    start_time = time.time()
    
    try:
        response = await call_next(request)
        response_time = time.time() - start_time
        
        metrics_collector.record_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            response_time=response_time
        )
        
        return response
    except Exception as e:
        response_time = time.time() - start_time
        metrics_collector.record_request(
            method=request.method,
            path=request.url.path,
            status_code=500,
            response_time=response_time
        )
        raise e

def get_prometheus_metrics() -> str:
    """Generate Prometheus-format metrics"""
    metrics = metrics_collector.get_all_metrics()
    
    prometheus_output = []
    
    # HTTP requests
    prometheus_output.append(f"# HELP http_requests_total Total HTTP requests")
    prometheus_output.append(f"# TYPE http_requests_total counter")
    prometheus_output.append(f"http_requests_total {metrics['requests']['total']}")
    
    # Response time
    prometheus_output.append(f"# HELP http_request_duration_seconds HTTP request duration")
    prometheus_output.append(f"# TYPE http_request_duration_seconds histogram")
    prometheus_output.append(f"http_request_duration_seconds_sum {sum(metrics['requests']['response_times'])}")
    prometheus_output.append(f"http_request_duration_seconds_count {len(metrics['requests']['response_times'])}")
    
    # System metrics
    prometheus_output.append(f"# HELP system_cpu_usage_percent CPU usage percentage")
    prometheus_output.append(f"# TYPE system_cpu_usage_percent gauge")
    prometheus_output.append(f"system_cpu_usage_percent {metrics['system']['cpu_percent']}")
    
    prometheus_output.append(f"# HELP system_memory_usage_percent Memory usage percentage")
    prometheus_output.append(f"# TYPE system_memory_usage_percent gauge")
    prometheus_output.append(f"system_memory_usage_percent {metrics['system']['memory_percent']}")
    
    # API calls
    for provider, stats in metrics['api_calls'].items():
        prometheus_output.append(f"# HELP api_calls_total Total API calls to {provider}")
        prometheus_output.append(f"# TYPE api_calls_total counter")
        prometheus_output.append(f"api_calls_total{{provider=\"{provider}\"}} {stats['total']}")
        
        prometheus_output.append(f"# HELP api_errors_total Total API errors for {provider}")
        prometheus_output.append(f"# TYPE api_errors_total counter")
        prometheus_output.append(f"api_errors_total{{provider=\"{provider}\"}} {stats['errors']}")
    
    # Content generation
    prometheus_output.append(f"# HELP content_campaigns_total Total content campaigns")
    prometheus_output.append(f"# TYPE content_campaigns_total counter")
    prometheus_output.append(f"content_campaigns_total {metrics['content_generation']['total_campaigns']}")
    
    prometheus_output.append(f"# HELP content_campaigns_successful_total Successful content campaigns")
    prometheus_output.append(f"# TYPE content_campaigns_successful_total counter")
    prometheus_output.append(f"content_campaigns_successful_total {metrics['content_generation']['successful_campaigns']}")
    
    return "\n".join(prometheus_output)