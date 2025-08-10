"""
Content templates for common use cases
"""
from typing import Dict, Any, List, Optional
from app.models import Platform, Tone
from app.logging_config import app_logger
from datetime import datetime

class ContentTemplates:
    """Pre-defined content templates for various scenarios"""
    
    def __init__(self):
        self.templates = {
            "product_launch": {
                "name": "Product Launch Announcement",
                "description": "Announce a new product or feature launch",
                "platforms": [Platform.LINKEDIN, Platform.FACEBOOK, Platform.TWITTER],
                "tone": Tone.INSPIRATIONAL,
                "prompt_template": """
                    Create an exciting announcement for the launch of {product}.
                    Target audience: {persona}
                    Key features: {features}
                    Launch date: {launch_date}
                    Special offer: {offer}
                    
                    Make it engaging and highlight the value proposition.
                    Include a strong call-to-action.
                """,
                "variables": ["product", "persona", "features", "launch_date", "offer"],
                "hashtags": ["launch", "newproduct", "innovation", "announcement"],
                "example_usage": {
                    "product": "AI Writing Assistant Pro",
                    "persona": "Content creators and marketers",
                    "features": "Advanced AI, real-time collaboration, 50+ templates",
                    "launch_date": "January 15, 2024",
                    "offer": "50% off for early adopters"
                }
            },
            
            "feature_update": {
                "name": "Feature Update",
                "description": "Announce new features or improvements",
                "platforms": [Platform.BLOG, Platform.EMAIL, Platform.LINKEDIN],
                "tone": Tone.EDUCATIONAL,
                "prompt_template": """
                    Write about the new features added to {product}.
                    New features: {features}
                    Benefits: {benefits}
                    How it works: {how_it_works}
                    Target users: {persona}
                    
                    Focus on the value these features bring to users.
                """,
                "variables": ["product", "features", "benefits", "how_it_works", "persona"],
                "hashtags": ["update", "newfeatures", "productupdate"],
                "example_usage": {
                    "product": "Project Management Tool",
                    "features": "AI task prioritization, automated reporting",
                    "benefits": "Save 5 hours per week on project management",
                    "how_it_works": "AI analyzes task dependencies and team capacity",
                    "persona": "Project managers and team leads"
                }
            },
            
            "thought_leadership": {
                "name": "Thought Leadership",
                "description": "Share industry insights and expertise",
                "platforms": [Platform.LINKEDIN, Platform.BLOG],
                "tone": Tone.PROFESSIONAL,
                "prompt_template": """
                    Write a thought leadership piece about {topic}.
                    Industry: {industry}
                    Key insights: {insights}
                    Data/statistics: {data}
                    Target audience: {persona}
                    
                    Position as an expert perspective with actionable insights.
                """,
                "variables": ["topic", "industry", "insights", "data", "persona"],
                "hashtags": ["thoughtleadership", "insights", "industry", "expertise"],
                "example_usage": {
                    "topic": "The Future of AI in Marketing",
                    "industry": "Digital Marketing",
                    "insights": "AI will automate 60% of content creation by 2025",
                    "data": "73% of marketers already use AI tools",
                    "persona": "Marketing executives and strategists"
                }
            },
            
            "case_study": {
                "name": "Case Study / Success Story",
                "description": "Share customer success stories and case studies",
                "platforms": [Platform.BLOG, Platform.LINKEDIN, Platform.FACEBOOK],
                "tone": Tone.INSPIRATIONAL,
                "prompt_template": """
                    Create a case study about {client} using {product}.
                    Challenge: {challenge}
                    Solution: {solution}
                    Results: {results}
                    Testimonial: {testimonial}
                    
                    Make it relatable and highlight measurable outcomes.
                """,
                "variables": ["client", "product", "challenge", "solution", "results", "testimonial"],
                "hashtags": ["casestudy", "successstory", "customerSuccess", "results"],
                "example_usage": {
                    "client": "TechStartup Inc.",
                    "product": "Cloud Analytics Platform",
                    "challenge": "Needed to reduce data processing time by 50%",
                    "solution": "Implemented our real-time analytics engine",
                    "results": "70% reduction in processing time, $2M saved annually",
                    "testimonial": "This platform transformed our data operations"
                }
            },
            
            "event_promotion": {
                "name": "Event Promotion",
                "description": "Promote webinars, conferences, or other events",
                "platforms": [Platform.TWITTER, Platform.LINKEDIN, Platform.FACEBOOK, Platform.EMAIL],
                "tone": Tone.FRIENDLY,
                "prompt_template": """
                    Promote the upcoming event: {event_name}
                    Date/Time: {date_time}
                    Format: {format}
                    Speakers: {speakers}
                    Key topics: {topics}
                    Registration link: {registration_link}
                    
                    Create urgency and highlight the value of attending.
                """,
                "variables": ["event_name", "date_time", "format", "speakers", "topics", "registration_link"],
                "hashtags": ["event", "webinar", "conference", "register"],
                "example_usage": {
                    "event_name": "AI Summit 2024",
                    "date_time": "March 15, 2024 at 2PM EST",
                    "format": "Virtual webinar",
                    "speakers": "Industry leaders from Google, Microsoft, OpenAI",
                    "topics": "Future of AI, Best practices, Case studies",
                    "registration_link": "example.com/register"
                }
            },
            
            "seasonal_campaign": {
                "name": "Seasonal Campaign",
                "description": "Holiday or seasonal promotional content",
                "platforms": [Platform.FACEBOOK, Platform.INSTAGRAM, Platform.EMAIL],
                "tone": Tone.CASUAL,
                "prompt_template": """
                    Create seasonal content for {season/holiday}.
                    Product/Service: {product}
                    Special offer: {offer}
                    Theme: {theme}
                    Target audience: {persona}
                    Duration: {duration}
                    
                    Make it festive and relevant to the season.
                """,
                "variables": ["season/holiday", "product", "offer", "theme", "persona", "duration"],
                "hashtags": ["seasonal", "holiday", "limitedtime", "specialoffer"],
                "example_usage": {
                    "season/holiday": "Black Friday",
                    "product": "All software subscriptions",
                    "offer": "60% off annual plans",
                    "theme": "Biggest sale of the year",
                    "persona": "Small business owners",
                    "duration": "November 24-27"
                }
            },
            
            "educational_content": {
                "name": "Educational Content",
                "description": "How-to guides, tutorials, and educational posts",
                "platforms": [Platform.BLOG, Platform.LINKEDIN, Platform.EMAIL],
                "tone": Tone.EDUCATIONAL,
                "prompt_template": """
                    Create educational content about {topic}.
                    Learning objective: {objective}
                    Key steps/points: {key_points}
                    Examples: {examples}
                    Target learner: {persona}
                    
                    Make it clear, actionable, and easy to follow.
                """,
                "variables": ["topic", "objective", "key_points", "examples", "persona"],
                "hashtags": ["howto", "tutorial", "learn", "education", "guide"],
                "example_usage": {
                    "topic": "How to implement AI in your marketing strategy",
                    "objective": "Learn to integrate AI tools effectively",
                    "key_points": "1. Assess needs, 2. Choose tools, 3. Train team, 4. Measure results",
                    "examples": "ChatGPT for content, Jasper for copy, Canva AI for design",
                    "persona": "Marketing managers new to AI"
                }
            },
            
            "partnership_announcement": {
                "name": "Partnership Announcement",
                "description": "Announce strategic partnerships or collaborations",
                "platforms": [Platform.LINKEDIN, Platform.TWITTER, Platform.BLOG],
                "tone": Tone.PROFESSIONAL,
                "prompt_template": """
                    Announce partnership between {company1} and {company2}.
                    Partnership purpose: {purpose}
                    Benefits for customers: {benefits}
                    Joint offerings: {offerings}
                    Quote from leadership: {quote}
                    
                    Emphasize synergies and customer value.
                """,
                "variables": ["company1", "company2", "purpose", "benefits", "offerings", "quote"],
                "hashtags": ["partnership", "collaboration", "announcement", "strategic"],
                "example_usage": {
                    "company1": "Our Company",
                    "company2": "Tech Giant Corp",
                    "purpose": "Integrate AI capabilities into our platform",
                    "benefits": "Faster processing, better insights, seamless workflow",
                    "offerings": "Joint AI-powered analytics solution",
                    "quote": "This partnership will revolutionize how businesses use data"
                }
            },
            
            "recruitment": {
                "name": "Recruitment / Hiring",
                "description": "Job postings and recruitment content",
                "platforms": [Platform.LINKEDIN, Platform.TWITTER, Platform.FACEBOOK],
                "tone": Tone.FRIENDLY,
                "prompt_template": """
                    Create a job posting for {position}.
                    Company: {company}
                    Team: {team}
                    Key responsibilities: {responsibilities}
                    Requirements: {requirements}
                    Benefits: {benefits}
                    Culture: {culture}
                    
                    Make it attractive to top talent and highlight company culture.
                """,
                "variables": ["position", "company", "team", "responsibilities", "requirements", "benefits", "culture"],
                "hashtags": ["hiring", "jobs", "careers", "recruitment", "opportunity"],
                "example_usage": {
                    "position": "Senior Software Engineer",
                    "company": "Innovation Tech",
                    "team": "Product Development",
                    "responsibilities": "Lead backend development, mentor junior developers",
                    "requirements": "5+ years Python, cloud experience, leadership skills",
                    "benefits": "Remote work, equity, unlimited PTO, learning budget",
                    "culture": "Collaborative, innovative, work-life balance focused"
                }
            },
            
            "customer_engagement": {
                "name": "Customer Engagement",
                "description": "Posts to engage with and gather feedback from customers",
                "platforms": [Platform.FACEBOOK, Platform.TWITTER, Platform.INSTAGRAM],
                "tone": Tone.CASUAL,
                "prompt_template": """
                    Create engaging content to interact with customers about {topic}.
                    Question/Poll: {question}
                    Context: {context}
                    Call to action: {cta}
                    Incentive: {incentive}
                    
                    Make it conversational and encourage participation.
                """,
                "variables": ["topic", "question", "context", "cta", "incentive"],
                "hashtags": ["community", "feedback", "poll", "engagement"],
                "example_usage": {
                    "topic": "Product feature preferences",
                    "question": "Which feature would you like to see next?",
                    "context": "We're planning our Q2 roadmap",
                    "cta": "Vote in the comments below",
                    "incentive": "Most requested feature gets priority development"
                }
            }
        }
    
    def get_template(self, template_key: str) -> Optional[Dict[str, Any]]:
        """Get a specific template by key"""
        template = self.templates.get(template_key)
        if template:
            app_logger.logger.info("template_retrieved", template_key=template_key)
        return template
    
    def list_templates(self) -> List[Dict[str, str]]:
        """List all available templates"""
        return [
            {
                "key": key,
                "name": template["name"],
                "description": template["description"],
                "platforms": [p.value for p in template["platforms"]]
            }
            for key, template in self.templates.items()
        ]
    
    def apply_template(
        self,
        template_key: str,
        variables: Dict[str, str]
    ) -> Optional[Dict[str, Any]]:
        """Apply variables to a template"""
        template = self.get_template(template_key)
        if not template:
            return None
        
        # Check if all required variables are provided
        missing_vars = set(template["variables"]) - set(variables.keys())
        if missing_vars:
            app_logger.logger.warning(
                "template_missing_variables",
                template_key=template_key,
                missing=list(missing_vars)
            )
            return None
        
        # Format the prompt with variables
        prompt = template["prompt_template"]
        for var, value in variables.items():
            prompt = prompt.replace(f"{{{var}}}", value)
        
        result = {
            "template_used": template_key,
            "name": template["name"],
            "prompt": prompt.strip(),
            "platforms": template["platforms"],
            "tone": template["tone"],
            "suggested_hashtags": template["hashtags"],
            "applied_at": datetime.utcnow().isoformat()
        }
        
        app_logger.logger.info(
            "template_applied",
            template_key=template_key,
            variables_count=len(variables)
        )
        
        return result
    
    def get_template_examples(self, template_key: str) -> Optional[Dict[str, Any]]:
        """Get example usage for a template"""
        template = self.get_template(template_key)
        if not template:
            return None
        
        return {
            "template": template_key,
            "name": template["name"],
            "example_variables": template.get("example_usage", {}),
            "required_variables": template["variables"],
            "platforms": [p.value for p in template["platforms"]],
            "tone": template["tone"].value
        }
    
    def search_templates(
        self,
        platform: Optional[Platform] = None,
        tone: Optional[Tone] = None
    ) -> List[str]:
        """Search templates by criteria"""
        results = []
        
        for key, template in self.templates.items():
            # Check platform match
            if platform and platform not in template["platforms"]:
                continue
            
            # Check tone match
            if tone and template["tone"] != tone:
                continue
            
            results.append(key)
        
        return results

# Global templates instance
content_templates = ContentTemplates()

# API models for template endpoints
from pydantic import BaseModel

class TemplateApplicationRequest(BaseModel):
    template_key: str
    variables: Dict[str, str]

class TemplateSearchRequest(BaseModel):
    platform: Optional[Platform] = None
    tone: Optional[Tone] = None

class TemplateResponse(BaseModel):
    template_used: str
    name: str
    prompt: str
    platforms: List[Platform]
    tone: Tone
    suggested_hashtags: List[str]
    applied_at: str