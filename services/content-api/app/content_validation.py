"""
Content validation and moderation for production safety
"""
from typing import Dict, List, Optional, Tuple
import re
from better_profanity import profanity
from langdetect import detect, LangDetectException
import bleach
from app.models import Platform
from app.logging_config import app_logger

# Platform-specific character limits
PLATFORM_LIMITS = {
    Platform.TWITTER: 280,
    Platform.LINKEDIN: 3000,
    Platform.FACEBOOK: 63206,
    Platform.INSTAGRAM: 2200,
    Platform.BLOG: 50000,
    Platform.EMAIL: 100000
}

# Initialize profanity filter
profanity.load_censor_words()

class ContentValidator:
    """Comprehensive content validation and moderation"""
    
    def __init__(self):
        # Patterns for detecting potentially harmful content
        self.spam_patterns = [
            r"(?i)(click here|buy now|limited time|act now|call now)",
            r"(?i)(guaranteed|100%|free money|no risk)",
            r"(?i)(viagra|cialis|pharmacy|pills)",
            r"(?i)(casino|lottery|winner|prize)",
            r"[A-Z]{5,}",  # Excessive caps
            r"(.)\1{4,}",  # Repeated characters
            r"https?://[^\s]+\s+https?://[^\s]+\s+https?://",  # Multiple URLs
        ]
        
        # Patterns for sensitive information
        self.sensitive_patterns = [
            r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
            r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",  # Credit card
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
            r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",  # Phone number
        ]
        
        # Blacklisted words/phrases (customize based on brand guidelines)
        self.blacklist = [
            "competitor_name",
            "inappropriate_term",
            "banned_phrase"
        ]
    
    async def validate_content(
        self,
        content: str,
        platform: Platform,
        strict_mode: bool = True
    ) -> Tuple[bool, List[str]]:
        """
        Validate content for a specific platform
        Returns: (is_valid, list_of_issues)
        """
        issues = []
        
        # Check length limits
        length_issue = self._check_length(content, platform)
        if length_issue:
            issues.append(length_issue)
        
        # Check for profanity
        if self._contains_profanity(content):
            issues.append("Content contains inappropriate language")
        
        # Check for spam patterns
        spam_issues = self._check_spam_patterns(content)
        if spam_issues:
            issues.extend(spam_issues)
        
        # Check for sensitive information
        if strict_mode:
            sensitive_issues = self._check_sensitive_info(content)
            if sensitive_issues:
                issues.extend(sensitive_issues)
        
        # Check language (ensure it's in expected language)
        lang_issue = self._check_language(content)
        if lang_issue:
            issues.append(lang_issue)
        
        # Check for blacklisted terms
        blacklist_issues = self._check_blacklist(content)
        if blacklist_issues:
            issues.extend(blacklist_issues)
        
        # Platform-specific checks
        platform_issues = self._platform_specific_checks(content, platform)
        if platform_issues:
            issues.extend(platform_issues)
        
        is_valid = len(issues) == 0
        
        # Log validation result
        app_logger.logger.info(
            "content_validation",
            platform=platform.value,
            is_valid=is_valid,
            issues_count=len(issues),
            content_length=len(content)
        )
        
        return is_valid, issues
    
    def _check_length(self, content: str, platform: Platform) -> Optional[str]:
        """Check if content exceeds platform limits"""
        limit = PLATFORM_LIMITS.get(platform, 10000)
        if len(content) > limit:
            return f"Content exceeds {platform.value} limit ({len(content)}/{limit} characters)"
        return None
    
    def _contains_profanity(self, content: str) -> bool:
        """Check for profanity in content"""
        return profanity.contains_profanity(content)
    
    def _check_spam_patterns(self, content: str) -> List[str]:
        """Check for spam-like patterns"""
        issues = []
        for pattern in self.spam_patterns:
            if re.search(pattern, content):
                issues.append(f"Content matches spam pattern: {pattern[:30]}...")
        return issues
    
    def _check_sensitive_info(self, content: str) -> List[str]:
        """Check for potentially sensitive information"""
        issues = []
        for pattern in self.sensitive_patterns:
            if re.search(pattern, content):
                issues.append("Content may contain sensitive information")
                break
        return issues
    
    def _check_language(self, content: str, expected_lang: str = "en") -> Optional[str]:
        """Check if content is in expected language"""
        try:
            detected_lang = detect(content)
            if detected_lang != expected_lang:
                return f"Content appears to be in {detected_lang}, expected {expected_lang}"
        except LangDetectException:
            return "Could not detect content language"
        return None
    
    def _check_blacklist(self, content: str) -> List[str]:
        """Check for blacklisted terms"""
        issues = []
        content_lower = content.lower()
        for term in self.blacklist:
            if term.lower() in content_lower:
                issues.append(f"Content contains blacklisted term: {term}")
        return issues
    
    def _platform_specific_checks(self, content: str, platform: Platform) -> List[str]:
        """Platform-specific validation rules"""
        issues = []
        
        if platform == Platform.TWITTER:
            # Check hashtag count
            hashtags = re.findall(r"#\w+", content)
            if len(hashtags) > 5:
                issues.append("Too many hashtags for Twitter (max 5 recommended)")
        
        elif platform == Platform.LINKEDIN:
            # Check for professional tone
            unprofessional_terms = ["lol", "omg", "wtf", "lmao"]
            for term in unprofessional_terms:
                if term.lower() in content.lower():
                    issues.append(f"Unprofessional language for LinkedIn: {term}")
        
        elif platform == Platform.EMAIL:
            # Check for required email elements
            if not re.search(r"unsubscribe", content, re.IGNORECASE):
                issues.append("Email missing unsubscribe link")
        
        return issues
    
    def sanitize_content(self, content: str) -> str:
        """Sanitize content to remove potentially harmful elements"""
        # Remove HTML tags except allowed ones
        allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li']
        allowed_attributes = {'a': ['href', 'title']}
        
        sanitized = bleach.clean(
            content,
            tags=allowed_tags,
            attributes=allowed_attributes,
            strip=True
        )
        
        # Clean up excessive whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        # Censor profanity if found
        if profanity.contains_profanity(sanitized):
            sanitized = profanity.censor(sanitized)
        
        return sanitized
    
    def suggest_improvements(self, content: str, platform: Platform) -> List[str]:
        """Suggest improvements for content"""
        suggestions = []
        
        # Check readability
        sentences = content.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        if avg_sentence_length > 20:
            suggestions.append("Consider using shorter sentences for better readability")
        
        # Check for call-to-action
        cta_patterns = ["learn more", "sign up", "get started", "try", "discover"]
        has_cta = any(pattern in content.lower() for pattern in cta_patterns)
        if not has_cta and platform in [Platform.FACEBOOK, Platform.LINKEDIN]:
            suggestions.append("Consider adding a clear call-to-action")
        
        # Check for engagement elements
        if platform == Platform.LINKEDIN and "?" not in content:
            suggestions.append("Consider asking a question to increase engagement")
        
        # Check hashtag usage
        hashtags = re.findall(r"#\w+", content)
        if platform in [Platform.LINKEDIN, Platform.TWITTER] and len(hashtags) == 0:
            suggestions.append("Consider adding relevant hashtags for better visibility")
        
        return suggestions

class ContentModerator:
    """Advanced content moderation using multiple checks"""
    
    def __init__(self):
        self.validator = ContentValidator()
        self.moderation_scores = {}
    
    async def moderate_content(
        self,
        content: str,
        platform: Platform,
        auto_fix: bool = False
    ) -> Dict[str, any]:
        """
        Moderate content and optionally fix issues
        Returns moderation result with score and fixes
        """
        # Validate content
        is_valid, issues = await self.validator.validate_content(content, platform)
        
        # Calculate moderation score (0-100, 100 being perfect)
        score = 100
        if issues:
            score -= min(len(issues) * 10, 50)
        
        # Check content quality
        quality_score = self._assess_quality(content, platform)
        score = (score + quality_score) / 2
        
        result = {
            "approved": score >= 70,
            "score": score,
            "issues": issues,
            "original_content": content
        }
        
        # Auto-fix if requested and possible
        if auto_fix and not result["approved"]:
            fixed_content = self.validator.sanitize_content(content)
            # Re-validate fixed content
            fixed_valid, fixed_issues = await self.validator.validate_content(fixed_content, platform)
            
            if len(fixed_issues) < len(issues):
                result["fixed_content"] = fixed_content
                result["fixed_issues"] = fixed_issues
                result["auto_fixed"] = True
        
        # Add suggestions
        result["suggestions"] = self.validator.suggest_improvements(content, platform)
        
        # Log moderation result
        app_logger.log_business_metric(
            "content_moderation_score",
            score,
            platform=platform.value,
            approved=result["approved"]
        )
        
        return result
    
    def _assess_quality(self, content: str, platform: Platform) -> float:
        """Assess content quality (0-100)"""
        score = 100.0
        
        # Check for minimum length
        min_lengths = {
            Platform.TWITTER: 50,
            Platform.LINKEDIN: 100,
            Platform.FACEBOOK: 80,
            Platform.BLOG: 300
        }
        
        min_length = min_lengths.get(platform, 50)
        if len(content) < min_length:
            score -= 20
        
        # Check for variety in vocabulary
        words = content.lower().split()
        unique_ratio = len(set(words)) / max(len(words), 1)
        if unique_ratio < 0.5:
            score -= 15
        
        # Check for proper capitalization
        if content.isupper() or content.islower():
            score -= 10
        
        # Check for emoji usage (good for social, bad for professional)
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            "]+", flags=re.UNICODE)
        
        has_emoji = bool(emoji_pattern.search(content))
        if platform == Platform.LINKEDIN and has_emoji:
            score -= 5
        elif platform in [Platform.FACEBOOK, Platform.INSTAGRAM] and not has_emoji:
            score -= 5
        
        return max(score, 0)

# Global instances
content_validator = ContentValidator()
content_moderator = ContentModerator()