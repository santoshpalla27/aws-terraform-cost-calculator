"""
Region and Availability Zone validation utilities.
"""
from typing import Dict, Any, List, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RegionValidator:
    """Validates and normalizes AWS regions and availability zones."""
    
    def __init__(self, aws_client_manager, cache):
        """
        Initialize region validator.
        
        Args:
            aws_client_manager: AWS client manager
            cache: Cache implementation
        """
        self.aws_client_manager = aws_client_manager
        self.cache = cache
        self._valid_regions: Optional[List[str]] = None
        self._az_cache: Dict[str, List[str]] = {}
    
    async def validate_region(self, region: str) -> bool:
        """
        Validate if region is a valid AWS region.
        
        Args:
            region: AWS region to validate
            
        Returns:
            True if valid
        """
        if not region:
            return False
        
        # Check cache
        cache_key = "aws:regions:all"
        cached_regions = await self.cache.get(cache_key)
        
        if cached_regions:
            return region in cached_regions
        
        # Call AWS API
        try:
            ec2_client = self.aws_client_manager.get_client('ec2', 'us-east-1')
            response = ec2_client.describe_regions(AllRegions=True)
            
            valid_regions = [r['RegionName'] for r in response.get('Regions', [])]
            
            # Cache for 24 hours (regions rarely change)
            await self.cache.set(cache_key, valid_regions, ttl=86400)
            
            logger.debug(f"Retrieved {len(valid_regions)} valid regions from AWS")
            
            return region in valid_regions
            
        except Exception as e:
            logger.error(f"Failed to validate region {region}: {e}")
            return False
    
    async def validate_availability_zone(
        self,
        az: str,
        region: str
    ) -> bool:
        """
        Validate if AZ is valid for the given region.
        
        Args:
            az: Availability zone
            region: AWS region
            
        Returns:
            True if valid
        """
        if not az or not region:
            return False
        
        # Check cache
        cache_key = f"aws:azs:{region}"
        cached_azs = await self.cache.get(cache_key)
        
        if cached_azs:
            return az in cached_azs
        
        # Call AWS API
        try:
            ec2_client = self.aws_client_manager.get_client('ec2', region)
            response = ec2_client.describe_availability_zones()
            
            valid_azs = [z['ZoneName'] for z in response.get('AvailabilityZones', [])]
            
            # Cache for 24 hours
            await self.cache.set(cache_key, valid_azs, ttl=86400)
            
            logger.debug(f"Retrieved {len(valid_azs)} AZs for region {region}")
            
            return az in valid_azs
            
        except Exception as e:
            logger.error(f"Failed to validate AZ {az} in region {region}: {e}")
            return False
    
    async def normalize_region(self, region: Optional[str]) -> Optional[str]:
        """
        Normalize and validate region.
        
        Args:
            region: Region to normalize
            
        Returns:
            Normalized region or None if invalid
        """
        if not region:
            return None
        
        # Normalize to lowercase
        normalized = region.lower().strip()
        
        # Validate
        is_valid = await self.validate_region(normalized)
        
        if not is_valid:
            logger.warning(f"Invalid region: {region}")
            return None
        
        return normalized
    
    async def get_region_from_az(self, az: str) -> Optional[str]:
        """
        Extract region from availability zone.
        
        Args:
            az: Availability zone (e.g., 'us-east-1a')
            
        Returns:
            Region (e.g., 'us-east-1') or None
        """
        if not az:
            return None
        
        # AZ format is typically {region}{zone-letter}
        # e.g., us-east-1a -> us-east-1
        parts = az.rsplit('-', 1)
        if len(parts) == 2:
            potential_region = parts[0]
            is_valid = await self.validate_region(potential_region)
            if is_valid:
                return potential_region
        
        return None
