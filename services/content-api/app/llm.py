from openai import AsyncOpenAI
from typing import List, Dict, Any, Optional
from app.config import settings
from app.models import Platform, Tone
import json

class ContentGenerator:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        
    async def generate_platform_content(
        self,
        product: str,
        persona: str,
        platform: Platform,
        tone: Tone,
        keywords: Optional[List[str]] = None,
        call_to_action: Optional[str] = None,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        
        platform_configs = {
            Platform.LINKEDIN: {
                "char_limit": 3000,
                "hashtag_count": 5,
                "style": "professional networking",
                "format": "thought leadership post"
            },
            Platform.FACEBOOK: {
                "char_limit": 500,
                "hashtag_count": 3,
                "style": "engaging and social",
                "format": "social media post with emoji"
            },
            Platform.INSTAGRAM: {
                "char_limit": 2200,
                "hashtag_count": 10,
                "style": "visual and inspiring",
                "format": "caption with storytelling"
            },
            Platform.TWITTER: {
                "char_limit": 280,
                "hashtag_count": 2,
                "style": "concise and punchy",
                "format": "tweet"
            }
        }
        
        config = platform_configs.get(platform, platform_configs[Platform.LINKEDIN])
        
        prompt = f"""
        Create a {config['format']} for {platform.value} about {product}.
        
        Target Audience: {persona}
        Tone: {tone.value}
        Style: {config['style']}
        Character Limit: {config['char_limit']}
        Hashtags: Include {config['hashtag_count']} relevant hashtags
        {'Keywords to include: ' + ', '.join(keywords) if keywords else ''}
        {'Call to Action: ' + call_to_action if call_to_action else 'Include a compelling call to action'}
        {'Additional Context: ' + context if context else ''}
        
        Format the response as JSON with the following structure:
        {{
            "content": "main post content",
            "hashtags": ["hashtag1", "hashtag2"],
            "headline": "optional headline for linkedin/blog",
            "media_suggestions": ["description of suggested images/videos"],
            "engagement_hooks": ["questions or prompts to drive engagement"]
        }}
        """
        
        if not self.client:
            # Fallback for testing without OpenAI API key
            return {
                "content": f"Introducing {product} - the perfect solution for {persona}. Experience the difference today!",
                "hashtags": ["innovation", "technology", platform.value],
                "headline": f"Revolutionize Your Approach with {product}",
                "media_suggestions": ["Product screenshot", "Happy customer testimonial"],
                "engagement_hooks": ["What's your biggest challenge?", "Share your experience below!"]
            }
        
        response = await self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "You are a expert content marketer and copywriter."},
                {"role": "user", "content": prompt}
            ],
            temperature=settings.openai_temperature,
            max_tokens=settings.openai_max_tokens,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def generate_blog_post(
        self,
        topic: str,
        target_audience: str,
        tone: Tone,
        word_count: int,
        keywords: Optional[List[str]] = None,
        sections: int = 5
    ) -> Dict[str, Any]:
        
        prompt = f"""
        Write a comprehensive blog post about: {topic}
        
        Target Audience: {target_audience}
        Tone: {tone.value}
        Word Count: Approximately {word_count} words
        Sections: {sections} main sections
        {'SEO Keywords to naturally include: ' + ', '.join(keywords) if keywords else ''}
        
        Format the response as JSON with:
        {{
            "title": "SEO-optimized title",
            "meta_description": "155-character meta description",
            "outline": ["Section 1", "Section 2", ...],
            "content": "Full blog post content with markdown formatting",
            "keywords": ["keyword1", "keyword2"],
            "estimated_reading_time": minutes,
            "word_count": actual_count
        }}
        """
        
        if not self.client:
            return {
                "title": f"The Ultimate Guide to {topic}",
                "meta_description": f"Discover everything you need to know about {topic} for {target_audience}.",
                "outline": ["Introduction", "Key Concepts", "Best Practices", "Common Mistakes", "Conclusion"],
                "content": f"# The Ultimate Guide to {topic}\n\n## Introduction\n\nContent about {topic}...",
                "keywords": keywords or ["guide", topic.lower()],
                "estimated_reading_time": word_count // 200,
                "word_count": word_count
            }
        
        response = await self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "You are an expert blog writer and SEO specialist."},
                {"role": "user", "content": prompt}
            ],
            temperature=settings.openai_temperature,
            max_tokens=min(settings.openai_max_tokens * 2, 4000),
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def generate_email_campaign(
        self,
        product: str,
        audience: str,
        campaign_type: str,
        tone: Tone,
        personalization_fields: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        
        prompt = f"""
        Create an email campaign for: {product}
        
        Campaign Type: {campaign_type}
        Target Audience: {audience}
        Tone: {tone.value}
        Personalization: {personalization_fields if personalization_fields else 'Use {{first_name}} and {{company}} tokens'}
        
        Format as JSON:
        {{
            "subject_lines": ["3-5 subject line options"],
            "preview_text": "Email preview text",
            "body_html": "Full HTML email body with personalization tokens",
            "body_text": "Plain text version",
            "personalization_tokens": ["list of tokens used"],
            "estimated_open_rate": 0.25
        }}
        """
        
        if not self.client:
            return {
                "subject_lines": [
                    f"Introducing {product} - Transform Your Business",
                    f"{{first_name}}, Discover {product} Today",
                    f"Exclusive Offer: {product} for {{company}}"
                ],
                "preview_text": f"See how {product} can help {audience}",
                "body_html": f"<h1>Welcome {{first_name}}!</h1><p>Introducing {product}...</p>",
                "body_text": f"Welcome {{first_name}}! Introducing {product}...",
                "personalization_tokens": ["first_name", "company"],
                "estimated_open_rate": 0.22
            }
        
        response = await self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "You are an expert email marketer."},
                {"role": "user", "content": prompt}
            ],
            temperature=settings.openai_temperature,
            max_tokens=settings.openai_max_tokens,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def generate_variations(
        self,
        base_content: str,
        platform: Platform,
        count: int = 3
    ) -> List[Dict[str, Any]]:
        
        prompt = f"""
        Create {count} variations of this {platform.value} content:
        
        Original: {base_content}
        
        Create variations that:
        - Maintain the same core message
        - Use different wording and structure
        - Target slightly different angles
        - Are suitable for A/B testing
        
        Format as JSON:
        {{
            "variations": [
                {{
                    "variation_id": "a",
                    "content": "variation content",
                    "changes": "what was changed"
                }}
            ]
        }}
        """
        
        if not self.client:
            return {
                "variations": [
                    {
                        "variation_id": f"var_{i}",
                        "content": f"Variation {i}: {base_content[:50]}...",
                        "changes": f"Variation {i} changes"
                    }
                    for i in range(1, count + 1)
                ]
            }
        
        response = await self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "You are an A/B testing expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=settings.openai_temperature + 0.2,  # Higher temperature for more variation
            max_tokens=settings.openai_max_tokens,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)["variations"]

content_generator = ContentGenerator()