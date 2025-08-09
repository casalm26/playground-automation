import httpx
from typing import Dict, Any, Optional, List
from app.config import settings
import json

class LinkedInAPI:
    """LinkedIn API integration for content posting and analytics"""
    
    def __init__(self):
        self.access_token = settings.linkedin_access_token
        self.base_url = "https://api.linkedin.com/v2"
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0"
            }
        )
    
    async def get_profile(self) -> Dict[str, Any]:
        """Get authenticated user's profile"""
        
        endpoint = f"{self.base_url}/me"
        
        try:
            response = await self.client.get(endpoint)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def post_content(
        self,
        text: str,
        author_urn: str,
        visibility: str = "PUBLIC",
        media_urls: Optional[List[str]] = None,
        article_link: Optional[str] = None,
        article_title: Optional[str] = None,
        article_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Post content to LinkedIn feed"""
        
        endpoint = f"{self.base_url}/ugcPosts"
        
        # Build the share content
        share_content = {
            "shareCommentary": {
                "text": text
            },
            "shareMediaCategory": "NONE"
        }
        
        # Add article if provided
        if article_link:
            share_content["shareMediaCategory"] = "ARTICLE"
            share_content["media"] = [{
                "status": "READY",
                "originalUrl": article_link,
                "title": {
                    "text": article_title or "Read More"
                },
                "description": {
                    "text": article_description or ""
                }
            }]
        
        # Add images if provided
        elif media_urls:
            share_content["shareMediaCategory"] = "IMAGE"
            share_content["media"] = []
            for url in media_urls:
                # In production, you'd need to upload images first
                share_content["media"].append({
                    "status": "READY",
                    "originalUrl": url
                })
        
        payload = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": share_content
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility
            }
        }
        
        try:
            response = await self.client.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def post_to_organization(
        self,
        organization_id: str,
        text: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        link: Optional[str] = None,
        visibility: str = "PUBLIC"
    ) -> Dict[str, Any]:
        """Post content to LinkedIn organization page"""
        
        endpoint = f"{self.base_url}/shares"
        
        payload = {
            "owner": f"urn:li:organization:{organization_id}",
            "text": {
                "text": text
            },
            "distribution": {
                "linkedInDistributionTarget": {
                    "visibleToGuest": visibility == "PUBLIC"
                }
            }
        }
        
        # Add content if link provided
        if link:
            payload["content"] = {
                "contentEntities": [{
                    "entityLocation": link,
                    "title": title or "Learn More",
                    "description": description or ""
                }]
            }
        
        try:
            response = await self.client.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def upload_image(
        self,
        owner_urn: str,
        image_data: bytes
    ) -> Dict[str, Any]:
        """Upload an image to LinkedIn for use in posts"""
        
        # Step 1: Register upload
        register_endpoint = f"{self.base_url}/assets?action=registerUpload"
        
        register_payload = {
            "registerUploadRequest": {
                "owner": owner_urn,
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "serviceRelationships": [{
                    "identifier": "urn:li:userGeneratedContent",
                    "relationshipType": "OWNER"
                }]
            }
        }
        
        try:
            # Register the upload
            register_response = await self.client.post(
                register_endpoint,
                json=register_payload
            )
            register_response.raise_for_status()
            register_data = register_response.json()
            
            if "value" not in register_data:
                return {"error": "Failed to register upload", "data": register_data}
            
            upload_url = register_data["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
            asset = register_data["value"]["asset"]
            
            # Step 2: Upload the image
            upload_response = await self.client.put(
                upload_url,
                content=image_data,
                headers={"Content-Type": "image/jpeg"}
            )
            upload_response.raise_for_status()
            
            return {
                "asset": asset,
                "status": "uploaded"
            }
            
        except httpx.HTTPError as e:
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def get_share_statistics(
        self,
        share_urn: str
    ) -> Dict[str, Any]:
        """Get statistics for a specific share"""
        
        endpoint = f"{self.base_url}/socialActions/{share_urn}"
        
        try:
            response = await self.client.get(
                endpoint,
                params={"q": "likes"}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def get_organization_statistics(
        self,
        organization_id: str,
        time_range_start: int,
        time_range_end: int
    ) -> Dict[str, Any]:
        """Get statistics for organization page"""
        
        endpoint = f"{self.base_url}/organizationalEntityShareStatistics"
        
        params = {
            "q": "organizationalEntity",
            "organizationalEntity": f"urn:li:organization:{organization_id}",
            "timeIntervals.timeGranularityType": "DAY",
            "timeIntervals.timeRange.start": time_range_start,
            "timeIntervals.timeRange.end": time_range_end
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
    
    async def create_campaign(
        self,
        account_id: str,
        name: str,
        objective: str = "WEBSITE_TRAFFIC",
        daily_budget: float = 50.0,
        status: str = "PAUSED"
    ) -> Dict[str, Any]:
        """Create LinkedIn ad campaign"""
        
        endpoint = "https://api.linkedin.com/v2/adCampaignsV2"
        
        payload = {
            "account": f"urn:li:sponsoredAccount:{account_id}",
            "name": name,
            "objective": objective,
            "costType": "CPM",
            "dailyBudget": {
                "amount": str(daily_budget),
                "currencyCode": "USD"
            },
            "status": status,
            "type": "SPONSORED_UPDATES"
        }
        
        try:
            response = await self.client.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def create_sponsored_content(
        self,
        account_id: str,
        campaign_id: str,
        share_urn: str,
        bid_amount: float = 10.0
    ) -> Dict[str, Any]:
        """Create sponsored content from existing share"""
        
        endpoint = "https://api.linkedin.com/v2/adCreativesV2"
        
        payload = {
            "campaign": f"urn:li:sponsoredCampaign:{campaign_id}",
            "reference": share_urn,
            "status": "ACTIVE",
            "type": "SPONSORED_STATUS_UPDATE",
            "variables": {
                "data": {
                    "com.linkedin.ads.SponsoredUpdateCreativeVariables": {
                        "activity": share_urn
                    }
                }
            }
        }
        
        try:
            response = await self.client.post(endpoint, json=payload)
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

linkedin_api = LinkedInAPI()