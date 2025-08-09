# Content Automation API Documentation

Version: 1.0.0  
Base URL: `https://api.yourdomain.com`

## Overview

The Content Automation API provides AI-powered content generation, multi-platform publishing, scheduling, and analytics for marketing campaigns. It integrates with OpenAI for content generation and supports Facebook, Instagram, LinkedIn, Twitter, blogs, and email campaigns.

## Authentication

All API endpoints (except health checks) require API key authentication via header:

```http
X-API-Key: your-secure-api-key-here
```

## Rate Limits

- General endpoints: 60 requests per minute
- Ad publishing endpoints: 10 requests per minute

## Base Endpoints

### Health & Status

#### GET /health
Returns detailed health status including system metrics and service health.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "uptime_seconds": 86400,
  "issues": [],
  "system": {
    "cpu_percent": 45.2,
    "memory_percent": 67.8,
    "disk_usage_percent": 23.5
  },
  "version": "1.0.0",
  "environment": "production"
}
```

#### GET /health/simple
Basic health check for load balancers.

**Response:**
```json
{
  "ok": true,
  "timestamp": "2024-01-15T10:30:00Z",
  "environment": "production"
}
```

#### GET /metrics
Returns comprehensive metrics in JSON format.

#### GET /metrics/prometheus
Returns metrics in Prometheus format for monitoring systems.

## Content Generation

### POST /generate-campaign
Generate multi-platform content for a marketing campaign.

**Request Body:**
```json
{
  "product": "AI Writing Assistant",
  "persona": "Content creators and marketers",
  "tone": "professional",
  "platforms": ["linkedin", "facebook", "twitter"],
  "keywords": ["AI", "writing", "productivity"],
  "call_to_action": "Try it free today",
  "context": "Launch announcement for new AI tool"
}
```

**Response:**
```json
{
  "campaign_id": "uuid-here",
  "generated_at": "2024-01-15T10:30:00Z",
  "content": {
    "linkedin": {
      "content": "Introducing our AI Writing Assistant...",
      "hashtags": ["#AI", "#Writing", "#Productivity"],
      "headline": "Revolutionary AI Writing Assistant",
      "media_suggestions": ["Product screenshot"],
      "engagement_hooks": ["What's your biggest writing challenge?"]
    },
    "facebook": {
      "content": "🚀 New AI tool alert! Our writing assistant...",
      "hashtags": ["#AI", "#Writing", "#Tech"],
      "media_suggestions": ["Demo video"]
    }
  },
  "variations": [
    {
      "variation_id": "uuid_a",
      "content": "Alternative version of LinkedIn content...",
      "hashtags": ["#AI", "#Writing", "#Productivity"]
    }
  ],
  "seo_keywords": ["AI", "writing", "productivity"],
  "estimated_reach": 23000
}
```

**Parameters:**
- `product` (string, required): Product or service name
- `persona` (string, required): Target audience description
- `tone` (string): Content tone - professional, casual, friendly, formal, humorous, inspirational, educational
- `platforms` (array): Target platforms - linkedin, facebook, instagram, twitter, blog, email
- `keywords` (array, optional): SEO keywords to include
- `call_to_action` (string, optional): Custom call to action
- `context` (string, optional): Additional context for content generation

### POST /generate-blog
Generate a complete blog post with SEO optimization.

**Request Body:**
```json
{
  "topic": "The Future of AI in Content Marketing",
  "target_audience": "Marketing professionals",
  "tone": "educational",
  "word_count": 1200,
  "keywords": ["AI marketing", "content automation"],
  "sections": 6
}
```

**Response:**
```json
{
  "title": "The Future of AI in Content Marketing: A Complete Guide",
  "meta_description": "Discover how AI is transforming content marketing...",
  "outline": [
    "Introduction: The AI Revolution",
    "Current State of AI in Marketing",
    "Key AI Technologies",
    "Implementation Strategies",
    "Future Trends",
    "Conclusion"
  ],
  "content": "# The Future of AI in Content Marketing\n\n## Introduction...",
  "keywords": ["AI marketing", "content automation", "machine learning"],
  "estimated_reading_time": 6,
  "word_count": 1247
}
```

### POST /generate-email
Generate email campaign content with personalization.

**Request Body:**
```json
{
  "product": "Marketing Automation Platform",
  "audience": "Small business owners",
  "campaign_type": "promotional",
  "tone": "friendly",
  "personalization_fields": {
    "first_name": "Name of recipient",
    "company": "Company name"
  },
  "variations_count": 3
}
```

**Response:**
```json
{
  "subject_lines": [
    "{{first_name}}, Grow Your Business with Automation",
    "Exclusive Offer for {{company}}",
    "Transform Your Marketing Today"
  ],
  "preview_text": "See how automation can boost your revenue",
  "body_html": "<h1>Hi {{first_name}}!</h1><p>Ready to transform {{company}}?</p>",
  "body_text": "Hi {{first_name}}! Ready to transform {{company}}?",
  "personalization_tokens": ["first_name", "company"],
  "estimated_open_rate": 0.24
}
```

## Ad Publishing

### POST /ads/publish
Queue an ad for publishing to advertising platforms.

**Request Body:**
```json
{
  "headline": "Boost Your Productivity with AI",
  "body": "Discover how our AI writing assistant can save you hours every week.",
  "url": "https://yourproduct.com/signup",
  "budget_daily": 50.00,
  "platform": "facebook",
  "target_audience": {
    "age_range": "25-45",
    "interests": ["marketing", "productivity"],
    "location": "United States"
  },
  "campaign_id": "optional-campaign-id"
}
```

**Response:**
```json
{
  "ad_id": "uuid-here",
  "status": "queued",
  "platform": "facebook",
  "preview": {
    "headline": "Boost Your Productivity with AI",
    "body": "Discover how our AI writing assistant...",
    "url": "https://yourproduct.com/signup"
  },
  "estimated_impressions": 50000,
  "estimated_clicks": 2500
}
```

## Webhooks & Callbacks

### POST /webhook/n8n
Receive webhooks from n8n workflows for event processing.

**Request Body:**
```json
{
  "event_type": "content_approved",
  "campaign_id": "uuid-here",
  "content_id": "optional-content-id",
  "platform": "linkedin",
  "status": "approved",
  "data": {
    "additional": "metadata"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### GET /webhook/status/{campaign_id}
Get webhook history for a specific campaign.

**Response:**
```json
{
  "campaign_id": "uuid-here",
  "webhook_count": 3,
  "webhooks": [
    {
      "event_type": "content_approved",
      "status": "approved",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ]
}
```

## Content Scheduling

### POST /schedule/content
Schedule content for future publishing.

**Request Body:**
```json
{
  "campaign_id": "uuid-here",
  "platform": "linkedin",
  "content": "Your scheduled post content here...",
  "scheduled_time": "2024-01-20T14:00:00Z",
  "metadata": {
    "hashtags": ["#marketing", "#AI"],
    "image_url": "https://example.com/image.jpg"
  }
}
```

### GET /schedule/pending
Get all pending scheduled content.

**Response:**
```json
{
  "count": 5,
  "content": [
    {
      "content_id": "uuid-here",
      "campaign_id": "uuid-here",
      "platform": "linkedin",
      "content": "Post content...",
      "scheduled_time": "2024-01-20T14:00:00Z",
      "status": "pending"
    }
  ]
}
```

## Analytics & Performance

### POST /analytics/performance
Track content performance metrics.

**Request Body:**
```json
{
  "content_id": "uuid-here",
  "platform": "linkedin",
  "impressions": 10000,
  "clicks": 500,
  "engagement_rate": 0.05,
  "conversions": 25,
  "cost": 50.00,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### GET /analytics/report/{campaign_id}
Get performance report for a specific campaign.

**Response:**
```json
{
  "campaign_id": "uuid-here",
  "total_impressions": 50000,
  "total_clicks": 2500,
  "engagement_rate": 0.05,
  "conversions": 125,
  "roi": 2.5,
  "top_platform": "linkedin",
  "best_performing_content": "variation_a",
  "cost_breakdown": {
    "linkedin": 100.00,
    "facebook": 75.00
  },
  "performance_by_platform": {
    "linkedin": {
      "impressions": 30000,
      "clicks": 1500,
      "conversions": 75
    }
  }
}
```

## Error Responses

All endpoints return structured error responses:

```json
{
  "error": "Invalid API key",
  "status_code": 401,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Common Error Codes
- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (missing/invalid API key)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found (resource doesn't exist)
- `429` - Too Many Requests (rate limit exceeded)
- `500` - Internal Server Error

## Platform-Specific Details

### LinkedIn Integration
- Requires LinkedIn OAuth token
- Supports personal and organization posting
- Analytics includes engagement metrics
- Image uploads supported

### Meta (Facebook/Instagram) Integration
- Uses Graph API v18.0
- Requires page access tokens
- Supports scheduled publishing
- Instagram requires business accounts

### Twitter Integration
- Uses Twitter API v2
- Character limits enforced
- Media attachments supported
- Rate limits apply

## Data Models

### Platform Enum
```
"linkedin" | "facebook" | "instagram" | "twitter" | "blog" | "email"
```

### Tone Enum
```
"professional" | "casual" | "friendly" | "formal" | "humorous" | "inspirational" | "educational"
```

### Campaign Status
```
"draft" | "pending" | "approved" | "published" | "rejected" | "failed"
```

## Integration Examples

### cURL Examples

#### Generate Campaign Content
```bash
curl -X POST "https://api.yourdomain.com/generate-campaign" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "product": "AI Assistant",
    "persona": "Developers",
    "platforms": ["linkedin", "twitter"]
  }'
```

#### Check Health
```bash
curl -X GET "https://api.yourdomain.com/health" \
  -H "X-API-Key: your-api-key"
```

### Python Example
```python
import requests

headers = {
    'X-API-Key': 'your-api-key',
    'Content-Type': 'application/json'
}

# Generate content
response = requests.post(
    'https://api.yourdomain.com/generate-campaign',
    headers=headers,
    json={
        'product': 'AI Writing Tool',
        'persona': 'Content creators',
        'platforms': ['linkedin', 'facebook']
    }
)

campaign = response.json()
print(f"Campaign ID: {campaign['campaign_id']}")
```

### Node.js Example
```javascript
const axios = require('axios');

const api = axios.create({
  baseURL: 'https://api.yourdomain.com',
  headers: {
    'X-API-Key': 'your-api-key',
    'Content-Type': 'application/json'
  }
});

// Generate blog post
const blogPost = await api.post('/generate-blog', {
  topic: 'AI in Marketing',
  target_audience: 'Marketing professionals',
  word_count: 800
});

console.log(blogPost.data.title);
```

## Webhook Integration with n8n

### Setting Up Webhooks
1. Configure webhook URLs in n8n workflows
2. Use authentication headers for security
3. Handle retry logic for failed webhooks
4. Monitor webhook delivery status

### Common Webhook Events
- `content_generated` - New content created
- `content_approved` - Content approved for publishing
- `content_published` - Content successfully published
- `performance_update` - Analytics data received
- `error_occurred` - System error or API failure

## Best Practices

### Authentication
- Store API keys securely
- Use environment variables
- Rotate keys regularly
- Monitor for unauthorized usage

### Rate Limiting
- Implement exponential backoff
- Cache responses when possible
- Monitor rate limit headers
- Use batch operations when available

### Error Handling
- Always check response status codes
- Implement retry logic for 5xx errors
- Log errors for debugging
- Provide meaningful user feedback

### Content Quality
- Review generated content before publishing
- Use human-in-the-loop approval
- Test with small audiences first
- Monitor performance metrics

### Security
- Validate all input data
- Use HTTPS only
- Implement CORS properly
- Monitor for suspicious activity

## Support & Troubleshooting

### Common Issues
1. **401 Unauthorized**: Check API key validity
2. **429 Rate Limited**: Reduce request frequency
3. **500 Server Error**: Check service health endpoint
4. **Empty responses**: Verify request parameters

### Monitoring
- Use `/health` endpoint for service status
- Monitor `/metrics` for performance data
- Set up alerts for error rates
- Track response times and availability

### Getting Help
1. Check API documentation
2. Verify request format and parameters
3. Test with simple requests first
4. Monitor error logs and metrics
5. Contact support with request details

## Changelog

### v1.0.0 (Current)
- Initial API release
- Multi-platform content generation
- n8n webhook integration
- Basic analytics and scheduling
- Health monitoring and metrics

### Upcoming Features
- Advanced analytics dashboard
- Image generation integration
- Multi-language support
- Enhanced A/B testing
- Custom model fine-tuning