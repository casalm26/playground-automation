from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime

class Platform(str, Enum):
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    BLOG = "blog"
    EMAIL = "email"

class Tone(str, Enum):
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    FRIENDLY = "friendly"
    FORMAL = "formal"
    HUMOROUS = "humorous"
    INSPIRATIONAL = "inspirational"
    EDUCATIONAL = "educational"

class CampaignIn(BaseModel):
    product: str = Field(..., description="Product or service name")
    persona: str = Field(..., description="Target audience description")
    tone: Tone = Field(default=Tone.PROFESSIONAL, description="Content tone")
    platforms: List[Platform] = Field(default=["linkedin"], description="Target platforms")
    keywords: Optional[List[str]] = Field(default=None, description="SEO keywords")
    call_to_action: Optional[str] = Field(default=None, description="Custom CTA")
    context: Optional[str] = Field(default=None, description="Additional context")

class ContentVariation(BaseModel):
    variation_id: str
    content: str
    hashtags: Optional[List[str]] = None
    media_suggestions: Optional[List[str]] = None

class CampaignOut(BaseModel):
    campaign_id: str
    generated_at: datetime
    content: Dict[str, Any]
    variations: Optional[List[ContentVariation]] = None
    seo_keywords: Optional[List[str]] = None
    estimated_reach: Optional[int] = None

class BlogPostIn(BaseModel):
    topic: str = Field(..., description="Blog post topic")
    target_audience: str = Field(..., description="Target audience")
    tone: Tone = Field(default=Tone.EDUCATIONAL)
    word_count: int = Field(default=800, ge=300, le=3000)
    keywords: Optional[List[str]] = None
    include_outline: bool = Field(default=True)
    sections: Optional[int] = Field(default=5, ge=3, le=10)

class BlogPostOut(BaseModel):
    title: str
    meta_description: str
    outline: Optional[List[str]] = None
    content: str
    keywords: List[str]
    estimated_reading_time: int
    word_count: int

class EmailCampaignIn(BaseModel):
    product: str
    audience: str
    campaign_type: str = Field(default="promotional", description="newsletter, promotional, announcement, etc.")
    tone: Tone = Field(default=Tone.FRIENDLY)
    personalization_fields: Optional[Dict[str, str]] = None
    include_subject_lines: bool = Field(default=True)
    variations_count: int = Field(default=1, ge=1, le=5)

class EmailCampaignOut(BaseModel):
    subject_lines: List[str]
    preview_text: str
    body_html: str
    body_text: str
    personalization_tokens: List[str]
    estimated_open_rate: Optional[float] = None

class AdIn(BaseModel):
    headline: str
    body: str
    url: str
    budget_daily: float
    platform: Platform
    target_audience: Optional[Dict[str, Any]] = None
    campaign_id: Optional[str] = None

class AdOut(BaseModel):
    ad_id: str
    status: str
    platform: str
    preview: Dict[str, Any]
    estimated_impressions: Optional[int] = None
    estimated_clicks: Optional[int] = None

class WebhookData(BaseModel):
    event_type: str = Field(..., description="Type of webhook event")
    campaign_id: Optional[str] = None
    content_id: Optional[str] = None
    platform: Optional[Platform] = None
    status: str
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ContentHistoryIn(BaseModel):
    campaign_id: str
    platform: Platform
    content: str
    metadata: Optional[Dict[str, Any]] = None

class PerformanceMetrics(BaseModel):
    content_id: str
    platform: Platform
    impressions: int = 0
    clicks: int = 0
    engagement_rate: float = 0.0
    conversions: int = 0
    cost: float = 0.0
    roi: Optional[float] = None
    timestamp: datetime

class ScheduledContent(BaseModel):
    content_id: str
    campaign_id: str
    platform: Platform
    content: str
    scheduled_time: datetime
    status: str = "pending"
    metadata: Optional[Dict[str, Any]] = None