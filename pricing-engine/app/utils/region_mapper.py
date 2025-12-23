"""
Region mapper for AWS pricing regions.
"""
from typing import Dict, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RegionMapper:
    """Maps AWS region codes to pricing region names."""
    
    # AWS region code to pricing region name mapping
    REGION_MAP: Dict[str, str] = {
        # US Regions
        'us-east-1': 'US East (N. Virginia)',
        'us-east-2': 'US East (Ohio)',
        'us-west-1': 'US West (N. California)',
        'us-west-2': 'US West (Oregon)',
        
        # Europe Regions
        'eu-west-1': 'EU (Ireland)',
        'eu-west-2': 'EU (London)',
        'eu-west-3': 'EU (Paris)',
        'eu-central-1': 'EU (Frankfurt)',
        'eu-north-1': 'EU (Stockholm)',
        'eu-south-1': 'EU (Milan)',
        
        # Asia Pacific Regions
        'ap-south-1': 'Asia Pacific (Mumbai)',
        'ap-northeast-1': 'Asia Pacific (Tokyo)',
        'ap-northeast-2': 'Asia Pacific (Seoul)',
        'ap-northeast-3': 'Asia Pacific (Osaka)',
        'ap-southeast-1': 'Asia Pacific (Singapore)',
        'ap-southeast-2': 'Asia Pacific (Sydney)',
        'ap-east-1': 'Asia Pacific (Hong Kong)',
        
        # Other Regions
        'ca-central-1': 'Canada (Central)',
        'sa-east-1': 'South America (Sao Paulo)',
        'me-south-1': 'Middle East (Bahrain)',
        'af-south-1': 'Africa (Cape Town)',
    }
    
    @classmethod
    def get_pricing_region(cls, region_code: str) -> Optional[str]:
        """
        Get pricing region name from AWS region code.
        
        Args:
            region_code: AWS region code (e.g., 'us-east-1')
            
        Returns:
            Pricing region name or None if not found
        """
        pricing_region = cls.REGION_MAP.get(region_code)
        
        if not pricing_region:
            logger.warning(f"Unknown region code: {region_code}")
        
        return pricing_region
    
    @classmethod
    def is_supported_region(cls, region_code: str) -> bool:
        """Check if region is supported."""
        return region_code in cls.REGION_MAP
    
    @classmethod
    def get_all_regions(cls) -> Dict[str, str]:
        """Get all supported regions."""
        return cls.REGION_MAP.copy()
