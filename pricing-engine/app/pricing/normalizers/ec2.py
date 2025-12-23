"""
EC2 pricing normalizer.
"""
from typing import List, Dict, Any
from datetime import datetime
from app.pricing.normalizers.base import BasePricingNormalizer
from app.schemas.pricing import NormalizedPrice, PricingUnit
from app.utils.logger import get_logger
from app.utils.region_mapper import RegionMapper

logger = get_logger(__name__)


class EC2PricingNormalizer(BasePricingNormalizer):
    """Normalizes EC2 pricing data."""
    
    def get_service_name(self) -> str:
        return "ec2"
    
    def normalize(self, pricing_data: Dict[str, Any], region: str) -> List[NormalizedPrice]:
        """
        Normalize EC2 pricing data.
        
        Args:
            pricing_data: Raw EC2 pricing data from AWS
            region: AWS region code
            
        Returns:
            List of normalized EC2 prices
        """
        normalized_prices = []
        
        # Get pricing region name
        pricing_region = RegionMapper.get_pricing_region(region)
        if not pricing_region:
            logger.warning(f"Unsupported region: {region}")
            return []
        
        products = pricing_data.get('products', {})
        terms = pricing_data.get('terms', {})
        
        for sku, product in products.items():
            # Only process products for the specified region
            product_attrs = product.get('attributes', {})
            if product_attrs.get('location') != pricing_region:
                continue
            
            # Only process instance types (not EBS, data transfer, etc.)
            product_family = product.get('productFamily', '')
            if product_family != 'Compute Instance':
                continue
            
            # Extract instance attributes
            instance_type = product_attrs.get('instanceType')
            if not instance_type:
                continue
            
            # Get pricing dimensions FOR THIS SKU ONLY
            sku_dimensions = self._extract_sku_pricing_dimensions(terms, sku)
            
            for dimension in sku_dimensions:
                # Only process hourly pricing
                unit = dimension.get('unit', '')
                if unit != 'Hrs':
                    continue
                
                price_per_unit = float(dimension.get('pricePerUnit', {}).get('USD', 0))
                
                normalized_price = NormalizedPrice(
                    service='ec2',
                    resource_type='instance',
                    usage_type=product_attrs.get('usagetype', ''),
                    region=region,
                    unit=PricingUnit.HOUR,
                    price_per_unit=price_per_unit,
                    currency='USD',
                    attributes={
                        'instanceType': instance_type,
                        'tenancy': product_attrs.get('tenancy', 'Shared'),
                        'operatingSystem': product_attrs.get('operatingSystem', 'Linux'),
                        'vcpu': product_attrs.get('vcpu'),
                        'memory': product_attrs.get('memory'),
                        'storage': product_attrs.get('storage'),
                        'networkPerformance': product_attrs.get('networkPerformance'),
                        'instanceFamily': product_attrs.get('instanceFamily'),
                        'currentGeneration': product_attrs.get('currentGeneration')
                    },
                    effective_date=datetime.utcnow(),
                    sku=sku
                )
                
                normalized_prices.append(normalized_price)
        
        logger.info(f"Normalized {len(normalized_prices)} EC2 prices for region {region}")
        
        return normalized_prices
