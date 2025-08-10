from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, Text, Float, Integer, DateTime, JSON, Enum, text
from sqlalchemy.pool import NullPool, QueuePool
from datetime import datetime
import enum
from contextlib import asynccontextmanager
from typing import Dict, Any

from app.config import settings
from app.logging_config import app_logger

Base = declarative_base()

# Create async engine with connection pooling
engine = None
AsyncSessionLocal = None

async def init_db():
    global engine, AsyncSessionLocal
    if settings.database_url:
        # Configure connection pooling
        engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            pool_size=20,  # Number of connections to maintain
            max_overflow=10,  # Maximum overflow connections
            pool_timeout=30,  # Timeout for getting connection from pool
            pool_recycle=3600,  # Recycle connections after 1 hour
            pool_pre_ping=True,  # Verify connections before use
        )
        
        AsyncSessionLocal = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        app_logger.logger.info(
            "database_initialized",
            pool_size=20,
            max_overflow=10
        )

async def get_db():
    if AsyncSessionLocal:
        async with AsyncSessionLocal() as session:
            yield session
    else:
        yield None

@asynccontextmanager
async def get_db_session():
    """Context manager for database sessions"""
    if AsyncSessionLocal:
        async with AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    else:
        yield None

async def check_database_health() -> Dict[str, Any]:
    """Check database health and connection pool status"""
    if not engine:
        return {"status": "not_configured", "healthy": False}
    
    try:
        # Test connection
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            await result.fetchone()
        
        # Get pool statistics
        pool = engine.pool
        pool_status = {
            "size": pool.size() if hasattr(pool, 'size') else 'N/A',
            "checked_in": pool.checkedin() if hasattr(pool, 'checkedin') else 'N/A',
            "checked_out": pool.checkedout() if hasattr(pool, 'checkedout') else 'N/A',
            "overflow": pool.overflow() if hasattr(pool, 'overflow') else 'N/A',
            "total": pool.total() if hasattr(pool, 'total') else 'N/A'
        }
        
        return {
            "status": "healthy",
            "healthy": True,
            "pool_status": pool_status
        }
    except Exception as e:
        app_logger.log_error("database_health_check_failed", str(e))
        return {
            "status": "unhealthy",
            "healthy": False,
            "error": str(e)
        }

# Database Models
class PlatformEnum(enum.Enum):
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    BLOG = "blog"
    EMAIL = "email"

class Campaign(Base):
    __tablename__ = "campaigns"
    
    id = Column(String, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    product = Column(String, nullable=False)
    persona = Column(String, nullable=False)
    tone = Column(String, nullable=False)
    content = Column(JSON)
    variations = Column(JSON)
    keywords = Column(JSON)
    estimated_reach = Column(Integer)

class ContentHistory(Base):
    __tablename__ = "content_history"
    
    id = Column(String, primary_key=True)
    campaign_id = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime)
    status = Column(String, default="draft")
    metadata = Column(JSON)

class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"
    
    id = Column(String, primary_key=True)
    content_id = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)
    conversions = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    roi = Column(Float)
    recorded_at = Column(DateTime, default=datetime.utcnow)

class ScheduledContentDB(Base):
    __tablename__ = "scheduled_content"
    
    content_id = Column(String, primary_key=True)
    campaign_id = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON)

class WebhookLog(Base):
    __tablename__ = "webhook_logs"
    
    id = Column(String, primary_key=True)
    event_type = Column(String, nullable=False)
    campaign_id = Column(String)
    content_id = Column(String)
    platform = Column(String)
    status = Column(String, nullable=False)
    data = Column(JSON)
    received_at = Column(DateTime, default=datetime.utcnow)