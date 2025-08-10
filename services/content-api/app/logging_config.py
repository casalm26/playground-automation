"""
Structured logging configuration for production
"""
import structlog
import logging
import sys
from datetime import datetime
from typing import Any, Dict
import json

def add_timestamp(_, __, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add timestamp to all log entries"""
    event_dict["timestamp"] = datetime.utcnow().isoformat()
    return event_dict

def add_severity(_, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add severity level based on method name"""
    severity_map = {
        "debug": "DEBUG",
        "info": "INFO",
        "warning": "WARNING",
        "error": "ERROR",
        "critical": "CRITICAL"
    }
    event_dict["severity"] = severity_map.get(method_name, "INFO")
    return event_dict

def add_correlation_id(_, __, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add correlation ID from context if available"""
    from contextvars import ContextVar
    correlation_id: ContextVar[str] = ContextVar('correlation_id', default='')
    
    if cid := correlation_id.get():
        event_dict["correlation_id"] = cid
    return event_dict

def setup_logging(log_level: str = "INFO", json_logs: bool = True):
    """Configure structured logging for the application"""
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper())
    )
    
    # Configure structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        add_timestamp,
        add_severity,
        add_correlation_id,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

class LoggerAdapter:
    """Adapter for consistent logging across the application"""
    
    def __init__(self, name: str):
        self.logger = structlog.get_logger(name)
    
    def log_api_request(self, method: str, path: str, **kwargs):
        """Log API request"""
        self.logger.info(
            "api_request",
            method=method,
            path=path,
            **kwargs
        )
    
    def log_api_response(self, status_code: int, response_time: float, **kwargs):
        """Log API response"""
        self.logger.info(
            "api_response",
            status_code=status_code,
            response_time_ms=response_time * 1000,
            **kwargs
        )
    
    def log_content_generation(self, platform: str, success: bool, generation_time: float, **kwargs):
        """Log content generation metrics"""
        self.logger.info(
            "content_generated",
            platform=platform,
            success=success,
            generation_time_s=generation_time,
            **kwargs
        )
    
    def log_external_api_call(self, service: str, endpoint: str, success: bool, response_time: float, **kwargs):
        """Log external API calls"""
        level = "info" if success else "warning"
        getattr(self.logger, level)(
            "external_api_call",
            service=service,
            endpoint=endpoint,
            success=success,
            response_time_ms=response_time * 1000,
            **kwargs
        )
    
    def log_error(self, error_type: str, error_message: str, **kwargs):
        """Log errors"""
        self.logger.error(
            "error_occurred",
            error_type=error_type,
            error_message=error_message,
            **kwargs
        )
    
    def log_business_metric(self, metric_name: str, value: float, **kwargs):
        """Log business metrics"""
        self.logger.info(
            "business_metric",
            metric_name=metric_name,
            value=value,
            **kwargs
        )
    
    def log_security_event(self, event_type: str, **kwargs):
        """Log security-related events"""
        self.logger.warning(
            "security_event",
            event_type=event_type,
            **kwargs
        )

# Create global logger instance
app_logger = LoggerAdapter("content_api")

# Middleware for request logging
from fastapi import Request, Response
import time
import uuid

async def logging_middleware(request: Request, call_next):
    """Middleware to log all requests and responses"""
    # Generate correlation ID
    correlation_id = str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    
    # Log request
    start_time = time.time()
    app_logger.log_api_request(
        method=request.method,
        path=request.url.path,
        correlation_id=correlation_id,
        client_host=request.client.host if request.client else None
    )
    
    try:
        # Process request
        response = await call_next(request)
        
        # Log response
        response_time = time.time() - start_time
        app_logger.log_api_response(
            status_code=response.status_code,
            response_time=response_time,
            correlation_id=correlation_id
        )
        
        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response
        
    except Exception as e:
        response_time = time.time() - start_time
        app_logger.log_error(
            error_type=type(e).__name__,
            error_message=str(e),
            correlation_id=correlation_id,
            response_time=response_time
        )
        raise