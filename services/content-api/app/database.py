from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, Text, Float, Integer, DateTime, JSON, Enum
from datetime import datetime
import enum

from app.config import settings

Base = declarative_base()

# Create async engine
engine = None
AsyncSessionLocal = None

async def init_db():
    global engine, AsyncSessionLocal
    if settings.database_url:
        engine = create_async_engine(settings.database_url, echo=settings.debug)
        AsyncSessionLocal = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

async def get_db():
    if AsyncSessionLocal:
        async with AsyncSessionLocal() as session:
            yield session
    else:
        yield None

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