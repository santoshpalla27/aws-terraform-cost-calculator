"""AWS Price List API client."""

import requests
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .config import settings

logger = logging.getLogger(__name__)


class PriceListClient:
    """Client for AWS Price List API."""
    
    def __init__(self, base_url: str = None):
        """Initialize client.
        
        Args:
            base_url: Price List API base URL
        """
        self.base_url = base_url or settings.price_list_base_url
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "AWS-Pricing-Engine/1.0"
        })
    
    def get_service_index(self) -> Dict[str, Any]:
        """Get service index from Price List API.
        
        Returns:
            Service index dictionary
        """
        url = f"{self.base_url}/offers/v1.0/aws/index.json"
        
        try:
            logger.info(f"Fetching service index from {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Retrieved {len(data.get('offers', {}))} services")
            
            return data
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch service index: {e}")
            raise
    
    def get_service_offer(self, service_code: str) -> Optional[Dict[str, Any]]:
        """Get pricing offer for a service.
        
        Args:
            service_code: Service code (e.g., AmazonEC2)
            
        Returns:
            Offer data or None
        """
        url = f"{self.base_url}/offers/v1.0/aws/{service_code}/current/index.json"
        
        try:
            logger.info(f"Fetching offer for {service_code}")
            response = self.session.get(url, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            
            products_count = len(data.get("products", {}))
            logger.info(f"Retrieved {products_count} products for {service_code}")
            
            return data
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch offer for {service_code}: {e}")
            return None
    
    def get_region_index(self) -> Dict[str, str]:
        """Get region index (location to region code mapping).
        
        Returns:
            Dictionary mapping location names to region codes
        """
        # AWS region mapping (commonly used)
        return {
            "US East (N. Virginia)": "us-east-1",
            "US East (Ohio)": "us-east-2",
            "US West (N. California)": "us-west-1",
            "US West (Oregon)": "us-west-2",
            "Europe (Ireland)": "eu-west-1",
            "Europe (London)": "eu-west-2",
            "Europe (Paris)": "eu-west-3",
            "Europe (Frankfurt)": "eu-central-1",
            "Asia Pacific (Singapore)": "ap-southeast-1",
            "Asia Pacific (Sydney)": "ap-southeast-2",
            "Asia Pacific (Tokyo)": "ap-northeast-1",
            "Asia Pacific (Mumbai)": "ap-south-1",
            "South America (São Paulo)": "sa-east-1",
            "Canada (Central)": "ca-central-1",
            "AWS GovCloud (US)": "us-gov-west-1",
        }
    
    def parse_offer(self, offer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse offer data into structured format.
        
        Args:
            offer_data: Raw offer data from API
            
        Returns:
            Parsed offer data
        """
        return {
            "format_version": offer_data.get("formatVersion"),
            "offer_code": offer_data.get("offerCode"),
            "version": offer_data.get("version"),
            "publication_date": offer_data.get("publicationDate"),
            "products": offer_data.get("products", {}),
            "terms": offer_data.get("terms", {})
        }
