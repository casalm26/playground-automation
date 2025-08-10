"""
Content preview functionality for different platforms
"""
from typing import Dict, Any, List, Optional
import re
from datetime import datetime
from app.models import Platform
from app.logging_config import app_logger

class ContentPreviewer:
    """Generate realistic previews of content for different platforms"""
    
    def __init__(self):
        # Platform-specific formatting rules
        self.platform_configs = {
            Platform.LINKEDIN: {
                "max_chars": 3000,
                "max_hashtags": 30,
                "supports_mentions": True,
                "supports_links": True,
                "link_preview": True,
                "character_counter": True
            },
            Platform.FACEBOOK: {
                "max_chars": 63206,
                "max_hashtags": 30,
                "supports_mentions": True,
                "supports_links": True,
                "link_preview": True,
                "character_counter": False
            },
            Platform.INSTAGRAM: {
                "max_chars": 2200,
                "max_hashtags": 30,
                "supports_mentions": True,
                "supports_links": False,  # Only in bio
                "link_preview": False,
                "character_counter": True
            },
            Platform.TWITTER: {
                "max_chars": 280,
                "max_hashtags": 10,
                "supports_mentions": True,
                "supports_links": True,
                "link_preview": True,
                "character_counter": True
            },
            Platform.BLOG: {
                "max_chars": 50000,
                "max_hashtags": 10,
                "supports_mentions": False,
                "supports_links": True,
                "link_preview": False,
                "character_counter": True,
                "supports_html": True
            },
            Platform.EMAIL: {
                "max_chars": 100000,
                "max_hashtags": 0,
                "supports_mentions": False,
                "supports_links": True,
                "link_preview": False,
                "character_counter": True,
                "supports_html": True
            }
        }
    
    def generate_preview(
        self,
        content: str,
        platform: Platform,
        hashtags: Optional[List[str]] = None,
        mentions: Optional[List[str]] = None,
        links: Optional[List[str]] = None,
        media_urls: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate a comprehensive preview for the specified platform"""
        
        config = self.platform_configs.get(platform, {})
        
        # Process content
        processed_content = self._process_content(content, platform, config)
        
        # Add hashtags
        if hashtags and platform != Platform.EMAIL:
            processed_content = self._add_hashtags(processed_content, hashtags, config)
        
        # Add mentions
        if mentions and config.get("supports_mentions"):
            processed_content = self._add_mentions(processed_content, mentions, platform)
        
        # Character count analysis
        char_analysis = self._analyze_character_count(processed_content, config)
        
        # Extract and format links
        link_analysis = self._analyze_links(links or [], config)
        
        # Media analysis
        media_analysis = self._analyze_media(media_urls or [], platform)
        
        # Generate platform-specific preview
        preview_html = self._generate_html_preview(
            processed_content, platform, config, char_analysis, link_analysis, media_analysis
        )
        
        # SEO and engagement analysis
        seo_analysis = self._analyze_seo(processed_content, hashtags or [])
        engagement_prediction = self._predict_engagement(processed_content, platform, hashtags or [])
        
        preview = {
            "platform": platform.value,
            "content": processed_content,
            "preview_html": preview_html,
            "character_analysis": char_analysis,
            "link_analysis": link_analysis,
            "media_analysis": media_analysis,
            "seo_analysis": seo_analysis,
            "engagement_prediction": engagement_prediction,
            "posting_tips": self._get_posting_tips(platform, char_analysis, hashtags or []),
            "generated_at": datetime.utcnow().isoformat()
        }
        
        app_logger.logger.info(
            "content_preview_generated",
            platform=platform.value,
            content_length=len(processed_content),
            character_status=char_analysis["status"]
        )
        
        return preview
    
    def _process_content(self, content: str, platform: Platform, config: Dict[str, Any]) -> str:
        """Process content according to platform rules"""
        processed = content.strip()
        
        # Platform-specific processing
        if platform == Platform.TWITTER:
            # Twitter-specific formatting
            processed = self._format_twitter_content(processed)
        elif platform == Platform.LINKEDIN:
            # LinkedIn professional formatting
            processed = self._format_linkedin_content(processed)
        elif platform == Platform.INSTAGRAM:
            # Instagram visual-first formatting
            processed = self._format_instagram_content(processed)
        elif platform in [Platform.BLOG, Platform.EMAIL]:
            # Rich text formatting
            processed = self._format_rich_content(processed)
        
        return processed
    
    def _format_twitter_content(self, content: str) -> str:
        """Format content for Twitter"""
        # Ensure content fits in tweets
        if len(content) > 280:
            # Truncate and add ellipsis
            content = content[:276] + "..."
        
        # Optimize for Twitter engagement
        content = re.sub(r'\n\n+', '\n\n', content)  # Max double line breaks
        return content
    
    def _format_linkedin_content(self, content: str) -> str:
        """Format content for LinkedIn"""
        # Professional formatting
        # Add line breaks for readability
        sentences = content.split('. ')
        if len(sentences) > 3:
            # Add paragraph breaks every 2-3 sentences
            formatted_sentences = []
            for i, sentence in enumerate(sentences):
                formatted_sentences.append(sentence)
                if i % 3 == 2 and i < len(sentences) - 1:
                    formatted_sentences.append('\n\n')
                elif i < len(sentences) - 1:
                    formatted_sentences.append('. ')
            content = ''.join(formatted_sentences)
        
        return content
    
    def _format_instagram_content(self, content: str) -> str:
        """Format content for Instagram"""
        # Instagram-friendly formatting
        # Add more line breaks for visual appeal
        content = re.sub(r'([.!?])\s+', r'\1\n\n', content, count=2)
        return content
    
    def _format_rich_content(self, content: str) -> str:
        """Format content for blog/email with HTML"""
        # Add basic HTML formatting
        paragraphs = content.split('\n\n')
        formatted = []
        
        for para in paragraphs:
            if para.strip():
                # Check if it looks like a heading
                if len(para) < 100 and para.endswith((':', '?', '!')):
                    formatted.append(f"<h3>{para.strip()}</h3>")
                else:
                    formatted.append(f"<p>{para.strip()}</p>")
        
        return '\n'.join(formatted)
    
    def _add_hashtags(self, content: str, hashtags: List[str], config: Dict[str, Any]) -> str:
        """Add hashtags to content"""
        max_hashtags = config.get("max_hashtags", 10)
        hashtags = hashtags[:max_hashtags]
        
        hashtag_str = " ".join(f"#{tag.lstrip('#')}" for tag in hashtags)
        
        # Add appropriate spacing
        if content and not content.endswith('\n'):
            content += '\n\n'
        
        return content + hashtag_str
    
    def _add_mentions(self, content: str, mentions: List[str], platform: Platform) -> str:
        """Add mentions to content"""
        # Platform-specific mention formatting
        mention_symbol = "@"
        
        for mention in mentions:
            mention_formatted = f"{mention_symbol}{mention.lstrip('@')}"
            # Replace placeholder or add at the end
            if "[mention]" in content:
                content = content.replace("[mention]", mention_formatted, 1)
            else:
                content = f"{mention_formatted} {content}"
        
        return content
    
    def _analyze_character_count(self, content: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze character count against platform limits"""
        char_count = len(content)
        max_chars = config.get("max_chars", 1000)
        
        # Determine status
        if char_count <= max_chars * 0.8:
            status = "good"
            color = "green"
        elif char_count <= max_chars:
            status = "warning"
            color = "orange"
        else:
            status = "over_limit"
            color = "red"
        
        return {
            "count": char_count,
            "limit": max_chars,
            "remaining": max_chars - char_count,
            "percentage": round((char_count / max_chars) * 100, 1),
            "status": status,
            "color": color,
            "counter_visible": config.get("character_counter", True)
        }
    
    def _analyze_links(self, links: List[str], config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze links in content"""
        return {
            "count": len(links),
            "links": links,
            "supports_links": config.get("supports_links", True),
            "link_preview": config.get("link_preview", False),
            "warnings": [
                "Links may not be clickable in Instagram posts"
            ] if not config.get("supports_links") else []
        }
    
    def _analyze_media(self, media_urls: List[str], platform: Platform) -> Dict[str, Any]:
        """Analyze media for platform compatibility"""
        media_limits = {
            Platform.TWITTER: {"images": 4, "videos": 1},
            Platform.FACEBOOK: {"images": 10, "videos": 1},
            Platform.INSTAGRAM: {"images": 10, "videos": 1},
            Platform.LINKEDIN: {"images": 9, "videos": 1}
        }
        
        limits = media_limits.get(platform, {"images": 5, "videos": 1})
        
        return {
            "count": len(media_urls),
            "media_urls": media_urls,
            "limits": limits,
            "warnings": [
                f"Maximum {limits['images']} images allowed"
            ] if len(media_urls) > limits['images'] else []
        }
    
    def _analyze_seo(self, content: str, hashtags: List[str]) -> Dict[str, Any]:
        """Analyze content for SEO factors"""
        # Extract key phrases
        words = re.findall(r'\w+', content.lower())
        word_count = len(words)
        
        # Simple keyword density calculation
        keyword_density = {}
        for hashtag in hashtags:
            tag = hashtag.lstrip('#').lower()
            count = content.lower().count(tag)
            if count > 0:
                keyword_density[tag] = round((count / word_count) * 100, 1)
        
        return {
            "word_count": word_count,
            "hashtag_count": len(hashtags),
            "keyword_density": keyword_density,
            "readability_score": self._calculate_readability(content),
            "seo_tips": [
                "Add more relevant hashtags" if len(hashtags) < 3 else None,
                "Content is too short for SEO" if word_count < 50 else None,
                "Consider adding more keywords" if not keyword_density else None
            ]
        }
    
    def _calculate_readability(self, content: str) -> float:
        """Simple readability score calculation"""
        sentences = len(re.split(r'[.!?]+', content))
        words = len(re.findall(r'\w+', content))
        
        if sentences == 0:
            return 0
        
        avg_sentence_length = words / sentences
        
        # Simple score: lower is more readable
        score = max(0, 100 - (avg_sentence_length - 15) * 2)
        return round(score, 1)
    
    def _predict_engagement(self, content: str, platform: Platform, hashtags: List[str]) -> Dict[str, Any]:
        """Predict engagement based on content characteristics"""
        
        # Basic engagement factors
        factors = {
            "content_length": len(content),
            "hashtag_count": len(hashtags),
            "question_marks": content.count('?'),
            "exclamation_marks": content.count('!'),
            "emojis": len(re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0002600-\U0002B55]', content))
        }
        
        # Platform-specific base rates
        base_rates = {
            Platform.LINKEDIN: 0.02,
            Platform.FACEBOOK: 0.05,
            Platform.INSTAGRAM: 0.08,
            Platform.TWITTER: 0.015,
            Platform.BLOG: 0.001,
            Platform.EMAIL: 0.20
        }
        
        base_rate = base_rates.get(platform, 0.03)
        
        # Adjust based on factors
        multiplier = 1.0
        
        # Length factor
        optimal_lengths = {
            Platform.LINKEDIN: (150, 300),
            Platform.FACEBOOK: (80, 200),
            Platform.INSTAGRAM: (138, 400),
            Platform.TWITTER: (71, 100)
        }
        
        if platform in optimal_lengths:
            min_len, max_len = optimal_lengths[platform]
            if min_len <= factors["content_length"] <= max_len:
                multiplier *= 1.3
            elif factors["content_length"] < min_len:
                multiplier *= 0.8
        
        # Hashtag factor
        if 1 <= factors["hashtag_count"] <= 5:
            multiplier *= 1.2
        elif factors["hashtag_count"] > 10:
            multiplier *= 0.9
        
        # Engagement elements
        if factors["question_marks"] > 0:
            multiplier *= 1.4
        if factors["emojis"] > 0 and platform != Platform.LINKEDIN:
            multiplier *= 1.1
        
        predicted_rate = base_rate * multiplier
        
        return {
            "predicted_engagement_rate": round(predicted_rate, 4),
            "confidence": 0.6,  # Low confidence as this is a simple model
            "factors_analyzed": factors,
            "engagement_score": min(100, round(predicted_rate * 1000, 1)),
            "tips": [
                "Add a question to increase engagement" if factors["question_marks"] == 0 else None,
                "Consider adding relevant hashtags" if factors["hashtag_count"] < 2 else None,
                "Content might be too long" if factors["content_length"] > optimal_lengths.get(platform, (0, 1000))[1] else None
            ]
        }
    
    def _get_posting_tips(self, platform: Platform, char_analysis: Dict[str, Any], hashtags: List[str]) -> List[str]:
        """Get platform-specific posting tips"""
        tips = []
        
        # Character count tips
        if char_analysis["status"] == "over_limit":
            tips.append(f"Content exceeds {platform.value} limit. Consider shortening.")
        elif char_analysis["status"] == "warning":
            tips.append("Close to character limit. Double-check before posting.")
        
        # Platform-specific tips
        if platform == Platform.LINKEDIN:
            tips.extend([
                "Post during business hours for better engagement",
                "Add line breaks for better readability",
                "Consider tagging relevant people or companies"
            ])
        elif platform == Platform.INSTAGRAM:
            tips.extend([
                "Include high-quality visuals",
                "Use relevant hashtags in comments for cleaner look",
                "Post during peak hours (6-8 PM)"
            ])
        elif platform == Platform.TWITTER:
            tips.extend([
                "Consider creating a thread if content is long",
                "Tweet during high-activity periods",
                "Engage with replies to boost visibility"
            ])
        
        # Hashtag tips
        if len(hashtags) == 0:
            tips.append("Consider adding hashtags to increase discoverability")
        elif len(hashtags) > 10:
            tips.append("Too many hashtags might look spammy")
        
        return [tip for tip in tips if tip]  # Filter out None values
    
    def _generate_html_preview(
        self,
        content: str,
        platform: Platform,
        config: Dict[str, Any],
        char_analysis: Dict[str, Any],
        link_analysis: Dict[str, Any],
        media_analysis: Dict[str, Any]
    ) -> str:
        """Generate HTML preview of how content will appear"""
        
        platform_styles = {
            Platform.LINKEDIN: {
                "container": "background: #f3f2ef; padding: 20px; border-radius: 8px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;",
                "content": "color: #000000; font-size: 14px; line-height: 1.5; white-space: pre-wrap;",
                "character_counter": f"color: {char_analysis['color']}; font-size: 12px; margin-top: 10px;"
            },
            Platform.TWITTER: {
                "container": "background: #ffffff; border: 1px solid #e1e8ed; border-radius: 12px; padding: 16px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px;",
                "content": "color: #0f1419; font-size: 15px; line-height: 1.3; white-space: pre-wrap;",
                "character_counter": f"color: {char_analysis['color']}; font-size: 13px; margin-top: 8px;"
            },
            Platform.FACEBOOK: {
                "container": "background: #ffffff; border: 1px solid #dddfe2; border-radius: 8px; padding: 16px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;",
                "content": "color: #1c1e21; font-size: 15px; line-height: 1.33; white-space: pre-wrap;",
                "character_counter": f"color: {char_analysis['color']}; font-size: 12px; margin-top: 8px;"
            },
            Platform.INSTAGRAM: {
                "container": "background: #ffffff; border: 1px solid #dbdbdb; border-radius: 3px; padding: 16px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 500px;",
                "content": "color: #262626; font-size: 14px; line-height: 1.5; white-space: pre-wrap;",
                "character_counter": f"color: {char_analysis['color']}; font-size: 12px; margin-top: 8px;"
            }
        }
        
        styles = platform_styles.get(platform, platform_styles[Platform.LINKEDIN])
        
        html = f"""
        <div style="{styles['container']}">
            <div style="{styles['content']}">{content}</div>
        """
        
        if char_analysis.get("counter_visible"):
            html += f"""
            <div style="{styles['character_counter']}">
                {char_analysis['count']}/{char_analysis['limit']} characters
            </div>
            """
        
        if media_analysis["count"] > 0:
            html += """
            <div style="margin-top: 12px; color: #666; font-size: 12px;">
                📷 Media attachments: """ + str(media_analysis["count"]) + """
            </div>
            """
        
        html += "</div>"
        
        return html

# Global content previewer
content_previewer = ContentPreviewer()