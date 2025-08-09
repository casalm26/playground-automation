import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.config import settings
import json

class MetaAPI:
    """Meta (Facebook/Instagram) Graph API integration"""
    
    def __init__(self):
        self.access_token = settings.meta_access_token
        self.base_url = "https://graph.facebook.com/v18.0"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def post_to_facebook(
        self,
        page_id: str,
        message: str,
        link: Optional[str] = None,
        image_url: Optional[str] = None,
        scheduled_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Post content to Facebook page"""
        
        endpoint = f"{self.base_url}/{page_id}/feed"
        
        params = {
            "access_token": self.access_token,
            "message": message
        }
        
        if link:
            params["link"] = link
        
        if scheduled_time and scheduled_time > datetime.utcnow():
            params["published"] = False
            params["scheduled_publish_time"] = int(scheduled_time.timestamp())
        
        try:
            if image_url:
                # First upload the photo
                photo_response = await self.upload_photo(page_id, image_url, message)
                return photo_response
            else:
                response = await self.client.post(endpoint, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def post_to_instagram(
        self,
        ig_user_id: str,
        image_url: str,
        caption: str,
        location_id: Optional[str] = None,
        user_tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Post content to Instagram Business account"""
        
        # Step 1: Create media container
        container_endpoint = f"{self.base_url}/{ig_user_id}/media"
        
        params = {
            "access_token": self.access_token,
            "image_url": image_url,
            "caption": caption
        }
        
        if location_id:
            params["location_id"] = location_id
        
        if user_tags:
            params["user_tags"] = json.dumps(user_tags)
        
        try:
            # Create container
            container_response = await self.client.post(container_endpoint, params=params)
            container_response.raise_for_status()
            container_data = container_response.json()
            
            if "id" not in container_data:
                return {"error": "Failed to create media container", "data": container_data}
            
            # Step 2: Publish the container
            publish_endpoint = f"{self.base_url}/{ig_user_id}/media_publish"
            publish_params = {
                "access_token": self.access_token,
                "creation_id": container_data["id"]
            }
            
            publish_response = await self.client.post(publish_endpoint, params=publish_params)
            publish_response.raise_for_status()
            
            return publish_response.json()
            
        except httpx.HTTPError as e:
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def upload_photo(
        self,
        page_id: str,
        photo_url: str,
        caption: str
    ) -> Dict[str, Any]:
        """Upload photo to Facebook page"""
        
        endpoint = f"{self.base_url}/{page_id}/photos"
        
        params = {
            "access_token": self.access_token,
            "url": photo_url,
            "caption": caption
        }
        
        try:
            response = await self.client.post(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def create_ad_campaign(
        self,
        ad_account_id: str,
        name: str,
        objective: str = "LINK_CLICKS",
        status: str = "PAUSED",
        budget_daily: Optional[float] = None
    ) -> Dict[str, Any]:
        """Create an ad campaign"""
        
        endpoint = f"{self.base_url}/act_{ad_account_id}/campaigns"
        
        params = {
            "access_token": self.access_token,
            "name": name,
            "objective": objective,
            "status": status,
            "special_ad_categories": "[]"
        }
        
        if budget_daily:
            params["daily_budget"] = int(budget_daily * 100)  # Convert to cents
        
        try:
            response = await self.client.post(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def create_ad_set(
        self,
        ad_account_id: str,
        campaign_id: str,
        name: str,
        daily_budget: float,
        targeting: Dict[str, Any],
        optimization_goal: str = "LINK_CLICKS"
    ) -> Dict[str, Any]:
        """Create an ad set with targeting"""
        
        endpoint = f"{self.base_url}/act_{ad_account_id}/adsets"
        
        params = {
            "access_token": self.access_token,
            "campaign_id": campaign_id,
            "name": name,
            "daily_budget": int(daily_budget * 100),
            "billing_event": "IMPRESSIONS",
            "optimization_goal": optimization_goal,
            "targeting": json.dumps(targeting),
            "status": "PAUSED"
        }
        
        try:
            response = await self.client.post(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def create_ad_creative(
        self,
        ad_account_id: str,
        name: str,
        page_id: str,
        headline: str,
        body: str,
        link: str,
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create ad creative"""
        
        endpoint = f"{self.base_url}/act_{ad_account_id}/adcreatives"
        
        object_story_spec = {
            "page_id": page_id,
            "link_data": {
                "link": link,
                "message": body,
                "name": headline,
                "call_to_action": {
                    "type": "LEARN_MORE"
                }
            }
        }
        
        if image_url:
            object_story_spec["link_data"]["picture"] = image_url
        
        params = {
            "access_token": self.access_token,
            "name": name,
            "object_story_spec": json.dumps(object_story_spec)
        }
        
        try:
            response = await self.client.post(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def get_page_insights(
        self,
        page_id: str,
        metrics: List[str] = None,
        period: str = "day"
    ) -> Dict[str, Any]:
        """Get page insights and analytics"""
        
        if metrics is None:
            metrics = [
                "page_impressions",
                "page_engaged_users",
                "page_post_engagements",
                "page_fans"
            ]
        
        endpoint = f"{self.base_url}/{page_id}/insights"
        
        params = {
            "access_token": self.access_token,
            "metric": ",".join(metrics),
            "period": period
        }
        
        try:
            response = await self.client.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def get_post_insights(
        self,
        post_id: str,
        metrics: List[str] = None
    ) -> Dict[str, Any]:
        """Get insights for a specific post"""
        
        if metrics is None:
            metrics = [
                "post_impressions",
                "post_engaged_users",
                "post_clicks",
                "post_reactions_by_type_total"
            ]
        
        endpoint = f"{self.base_url}/{post_id}/insights"
        
        params = {
            "access_token": self.access_token,
            "metric": ",".join(metrics)
        }
        
        try:
            response = await self.client.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

meta_api = MetaAPI()