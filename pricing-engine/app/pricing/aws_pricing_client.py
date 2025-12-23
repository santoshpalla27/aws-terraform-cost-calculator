"""
AWS Pricing API client.
"""
import httpx
from typing import Dict, Any, Optional
from datetime import datetime
from app.utils.logger import get_logger
from app.config import settings

logger = get_logger(__name__)


class AWSPricingClient:
    """Client for AWS Price List API."""
    
    def __init__(self, base_url: str = None):
        """
        Initialize AWS Pricing Client.
        
        Args:
            base_url: Base URL for AWS Pricing API
        """
        self.base_url = base_url or settings.pricing_api_base_url
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def fetch_service_pricing(self, service: str) -> Dict[str, Any]:
        """
        Fetch pricing data for a service from AWS Price List API.
        
        Args:
            service: AWS service name (ec2, ebs, elb, etc.)
            
        Returns:
            Dict containing pricing data
            
        Raises:
            httpx.HTTPError: If API request fails
        """
        # Map service names to AWS pricing service codes
        service_map = {
            'ec2': 'AmazonEC2',
            'ebs': 'AmazonEC2',  # EBS is part of EC2 pricing
            'elb': 'AmazonEC2',  # ELB is part of EC2 pricing  
            'rds': 'AmazonRDS',
            'nat': 'AmazonEC2',  # NAT Gateway is part of EC2
            'cloudwatch': 'AmazonCloudWatch',
            'eks': 'AmazonEKS'
        }
        
        service_code = service_map.get(service, service)
        url = f"{self.base_url}/offers/v1.0/aws/{service_code}/current/index.json"
        
        logger.info(f"Fetching pricing for service: {service} from {url}")
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Successfully fetched pricing for {service}")
            
            return data
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch pricing for {service}: {e}")
            raise
    
    async def get_pricing_metadata(self, service: str) -> Dict[str, Any]:
        """
        Get pricing metadata (version, publication date) for a service.
        
        Args:
            service: AWS service name
            
        Returns:
            Dict with metadata
        """
        try:
            data = await self.fetch_service_pricing(service)
            
            metadata = {
                'service': service,
                'version': data.get('version', 'unknown'),
                'publication_date': data.get('publicationDate', ''),
                'format_version': data.get('formatVersion', ''),
                'offer_code': data.get('offerCode', '')
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to get metadata for {service}: {e}")
            return {}
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
