from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
from datetime import datetime
import uuid
import time
from typing import Dict, Any, List

from app.config import settings
from app.auth import verify_api_key
from app.models import (
    CampaignIn, CampaignOut, BlogPostIn, BlogPostOut,
    EmailCampaignIn, EmailCampaignOut, AdIn, AdOut,
    WebhookData, ContentHistoryIn, PerformanceMetrics,
    ScheduledContent, Platform, ContentVariation
)
from app.llm import content_generator
from app.database import init_db, get_db
from app.monitoring import metrics_middleware, metrics_collector, get_prometheus_metrics

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if settings.database_url:
        await init_db()
    yield
    # Shutdown
    pass

app = FastAPI(
    title="Content Automation API",
    version="1.0.0",
    description="AI-powered content generation and marketing automation API",
    lifespan=lifespan
)

# Add rate limit error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Metrics middleware
app.middleware("http")(metrics_middleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage for webhooks and scheduled content (in production, use database)
webhook_store: Dict[str, List[WebhookData]] = {}
scheduled_content_store: Dict[str, ScheduledContent] = {}

@app.get("/")
def root():
    return {
        "name": "Content Automation API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
def health():
    health_status = metrics_collector.get_health_status()
    return health_status

@app.get("/health/simple")
def health_simple():
    return {
        "ok": True,
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment
    }

@app.get("/metrics")
def get_metrics():
    return metrics_collector.get_all_metrics()

@app.get("/metrics/prometheus")
def get_prometheus_metrics_endpoint():
    return Response(
        content=get_prometheus_metrics(),
        media_type="text/plain"
    )

@app.post("/generate-campaign", response_model=CampaignOut)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def generate_campaign(
    request: any,  # Required for rate limiter
    data: CampaignIn,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """Generate content for multiple platforms"""
    start_time = time.time()
    campaign_id = str(uuid.uuid4())
    content = {}
    variations = []
    success = False
    
    try:
        # Generate content for each platform
        for platform in data.platforms:
            platform_content = await content_generator.generate_platform_content(
                product=data.product,
                persona=data.persona,
                platform=platform,
                tone=data.tone,
                keywords=data.keywords,
                call_to_action=data.call_to_action,
                context=data.context
            )
            content[platform.value] = platform_content
            
            # Generate variations for A/B testing if it's a primary platform
            if platform in [Platform.LINKEDIN, Platform.FACEBOOK]:
                platform_variations = await content_generator.generate_variations(
                    base_content=platform_content["content"],
                    platform=platform,
                    count=2
                )
                for var in platform_variations:
                    variations.append(ContentVariation(
                        variation_id=f"{campaign_id}_{var['variation_id']}",
                        content=var["content"],
                        hashtags=platform_content.get("hashtags"),
                        media_suggestions=platform_content.get("media_suggestions")
                    ))
        
        # Store campaign history (in production, save to database)
        background_tasks.add_task(store_campaign_history, campaign_id, content)
        success = True
        
        return CampaignOut(
            campaign_id=campaign_id,
            generated_at=datetime.utcnow(),
            content=content,
            variations=variations if variations else None,
            seo_keywords=data.keywords,
            estimated_reach=calculate_estimated_reach(data.platforms)
        )
    except Exception as e:
        raise e
    finally:
        generation_time = time.time() - start_time
        metrics_collector.record_content_generation(success, generation_time)

@app.post("/generate-blog", response_model=BlogPostOut)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def generate_blog_post(
    request: any,
    data: BlogPostIn,
    api_key: str = Depends(verify_api_key)
):
    """Generate a complete blog post with SEO optimization"""
    result = await content_generator.generate_blog_post(
        topic=data.topic,
        target_audience=data.target_audience,
        tone=data.tone,
        word_count=data.word_count,
        keywords=data.keywords,
        sections=data.sections
    )
    
    return BlogPostOut(**result)

@app.post("/generate-email", response_model=EmailCampaignOut)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def generate_email_campaign(
    request: any,
    data: EmailCampaignIn,
    api_key: str = Depends(verify_api_key)
):
    """Generate email campaign content with personalization"""
    result = await content_generator.generate_email_campaign(
        product=data.product,
        audience=data.audience,
        campaign_type=data.campaign_type,
        tone=data.tone,
        personalization_fields=data.personalization_fields
    )
    
    # Generate variations if requested
    if data.variations_count > 1:
        base_subject = result["subject_lines"][0]
        for i in range(1, data.variations_count):
            result["subject_lines"].append(f"Variation {i}: {base_subject}")
    
    return EmailCampaignOut(**result)

@app.post("/ads/publish", response_model=AdOut)
@limiter.limit("10/minute")
async def publish_ad(
    request: any,
    ad: AdIn,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """Queue an ad for publishing to the specified platform"""
    ad_id = str(uuid.uuid4())
    
    # In production, this would call actual ad platform APIs
    # For now, we'll simulate the process
    background_tasks.add_task(process_ad_publishing, ad_id, ad)
    
    return AdOut(
        ad_id=ad_id,
        status="queued",
        platform=ad.platform.value,
        preview=ad.dict(),
        estimated_impressions=calculate_estimated_impressions(ad.budget_daily),
        estimated_clicks=calculate_estimated_clicks(ad.budget_daily)
    )

@app.post("/webhook/n8n")
async def n8n_webhook(
    data: WebhookData,
    background_tasks: BackgroundTasks
):
    """Receive webhooks from n8n workflows"""
    webhook_id = str(uuid.uuid4())
    
    # Store webhook data
    if data.campaign_id not in webhook_store:
        webhook_store[data.campaign_id] = []
    webhook_store[data.campaign_id].append(data)
    
    # Process webhook based on event type
    if data.event_type == "content_approved":
        background_tasks.add_task(publish_approved_content, data)
    elif data.event_type == "performance_update":
        background_tasks.add_task(update_performance_metrics, data)
    
    return {"webhook_id": webhook_id, "status": "received"}

@app.get("/webhook/status/{campaign_id}")
async def get_webhook_status(
    campaign_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get webhook history for a campaign"""
    webhooks = webhook_store.get(campaign_id, [])
    return {
        "campaign_id": campaign_id,
        "webhook_count": len(webhooks),
        "webhooks": [w.dict() for w in webhooks]
    }

@app.post("/schedule/content")
async def schedule_content(
    content: ScheduledContent,
    api_key: str = Depends(verify_api_key)
):
    """Schedule content for future publishing"""
    content_id = str(uuid.uuid4())
    content.content_id = content_id
    scheduled_content_store[content_id] = content
    
    return {
        "content_id": content_id,
        "scheduled_time": content.scheduled_time,
        "status": "scheduled"
    }

@app.get("/schedule/pending")
async def get_pending_content(
    api_key: str = Depends(verify_api_key)
):
    """Get all pending scheduled content"""
    now = datetime.utcnow()
    pending = [
        c.dict() for c in scheduled_content_store.values()
        if c.status == "pending" and c.scheduled_time > now
    ]
    return {"count": len(pending), "content": pending}

@app.post("/analytics/performance")
async def track_performance(
    metrics: PerformanceMetrics,
    api_key: str = Depends(verify_api_key)
):
    """Track content performance metrics"""
    # In production, save to database
    return {
        "status": "tracked",
        "content_id": metrics.content_id,
        "roi": calculate_roi(metrics.cost, metrics.conversions)
    }

@app.get("/analytics/report/{campaign_id}")
async def get_campaign_report(
    campaign_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get performance report for a campaign"""
    # In production, aggregate from database
    return {
        "campaign_id": campaign_id,
        "total_impressions": 10000,
        "total_clicks": 500,
        "engagement_rate": 0.05,
        "conversions": 25,
        "roi": 2.5,
        "top_platform": "linkedin",
        "best_performing_content": "variation_a"
    }

# Helper functions
async def store_campaign_history(campaign_id: str, content: Dict[str, Any]):
    """Store campaign content in database"""
    # In production, save to database
    pass

async def process_ad_publishing(ad_id: str, ad: AdIn):
    """Process ad publishing to platform APIs"""
    # In production, call actual platform APIs
    pass

async def publish_approved_content(data: WebhookData):
    """Publish content that has been approved"""
    # In production, trigger publishing workflow
    pass

async def update_performance_metrics(data: WebhookData):
    """Update performance metrics from platform data"""
    # In production, fetch and store metrics
    pass

def calculate_estimated_reach(platforms: List[Platform]) -> int:
    """Calculate estimated reach based on platforms"""
    base_reach = {
        Platform.LINKEDIN: 5000,
        Platform.FACEBOOK: 8000,
        Platform.INSTAGRAM: 10000,
        Platform.TWITTER: 3000,
        Platform.BLOG: 2000,
        Platform.EMAIL: 1000
    }
    return sum(base_reach.get(p, 1000) for p in platforms)

def calculate_estimated_impressions(budget: float) -> int:
    """Calculate estimated impressions based on budget"""
    return int(budget * 1000)  # $1 = ~1000 impressions

def calculate_estimated_clicks(budget: float) -> int:
    """Calculate estimated clicks based on budget"""
    return int(budget * 50)  # $1 = ~50 clicks

def calculate_roi(cost: float, conversions: int, value_per_conversion: float = 100) -> float:
    """Calculate ROI"""
    if cost == 0:
        return 0
    revenue = conversions * value_per_conversion
    return (revenue - cost) / cost

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)