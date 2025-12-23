"""
EBS pricing normalizer.
"""
from typing import List, Dict, Any
from datetime import datetime
from app.pricing.normalizers.base import BasePricingNormalizer
from app.schemas.pricing import NormalizedPrice, PricingUnit
from app.utils.logger import get_logger
from app.utils.region_mapper import RegionMapper

logger = get_logger(__name__)


class EBSPricingNormalizer(BasePricingNormalizer):
    """Normalizes EBS pricing data."""
    
    def get_service_name(self) -> str:
        return "ebs"
    
    def normalize(self, pricing_data: Dict[str, Any], region: str) -> List[NormalizedPrice]:
        """
        Normalize EBS pricing data.
        
        Args:
            pricing_data: Raw EBS pricing data from AWS (part of EC2 pricing)
            region: AWS region code
            
        Returns:
            List of normalized EBS prices
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
            
            # Only process EBS storage
            product_family = product.get('productFamily', '')
            if product_family != 'Storage':
                continue
            
            # Extract volume type
            volume_type = product_attrs.get('volumeApiName', product_attrs.get('volumeType', ''))
            if not volume_type:
                continue
            
            # Get pricing dimensions
            dimensions = self._extract_pricing_dimensions(terms)
            
            for dimension in dimensions:
                unit = dimension.get('unit', '')
                
                # Determine resource type and pricing unit
                if 'snapshot' in product_attrs.get('usagetype', '').lower():
                    resource_type = 'snapshot'
                    pricing_unit = PricingUnit.GB_MONTH
                else:
                    resource_type = 'volume'
                    pricing_unit = PricingUnit.GB_MONTH
                
                price_per_unit = float(dimension.get('pricePerUnit', {}).get('USD', 0))
                
                normalized_price = NormalizedPrice(
                    service='ebs',
                    resource_type=resource_type,
                    usage_type=product_attrs.get('usagetype', ''),
                    region=region,
                    unit=pricing_unit,
                    price_per_unit=price_per_unit,
                    currency='USD',
                    attributes={
                        'volumeType': volume_type,
                        'volumeApiName': product_attrs.get('volumeApiName'),
                        'storageMedia': product_attrs.get('storageMedia'),
                        'maxIopsvolume': product_attrs.get('maxIopsvolume'),
                        'maxThroughputvolume': product_attrs.get('maxThroughputvolume')
                    },
                    effective_date=datetime.utcnow(),
                    sku=sku
                )
                
                normalized_prices.append(normalized_price)
        
        logger.info(f"Normalized {len(normalized_prices)} EBS prices for region {region}")
        
        return normalized_prices
