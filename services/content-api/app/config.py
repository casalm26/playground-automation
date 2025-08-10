from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Keys
    openai_api_key: str = ""
    meta_access_token: str = ""
    linkedin_access_token: str = ""
    google_ads_api_key: str = ""
    
    # API Authentication
    api_key: str = "change-me-to-secure-key"
    api_key_header: str = "X-API-Key"
    
    # Database
    database_url: Optional[str] = "postgresql+asyncpg://app:password@postgres-app/automation"
    
    # Redis (for caching and queuing)
    redis_url: str = "redis://redis:6379"
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    
    # OpenAI Settings
    openai_model: str = "gpt-4-turbo-preview"
    openai_temperature: float = 0.7
    openai_max_tokens: int = 2000
    
    # Production Features
    enable_content_moderation: bool = True
    enable_caching: bool = True
    enable_usage_tracking: bool = True
    enable_webhooks: bool = True
    
    # Usage Limits
    daily_request_limit: int = 1000
    daily_token_limit: int = 1000000
    daily_cost_limit: float = 50.0
    
    # Webhook Settings
    webhook_timeout: int = 30
    webhook_retry_attempts: int = 3
    
    # Content Settings
    max_content_length: int = 4000
    content_cache_ttl: int = 3600
    
    # Logging
    log_level: str = "INFO"
    json_logs: bool = True
    
    # Environment
    environment: str = "development"
    debug: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()