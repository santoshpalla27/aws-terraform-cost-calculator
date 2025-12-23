"""
RDS pricing normalizer.
"""
from typing import List, Dict, Any
from datetime import datetime
from app.pricing.normalizers.base import BasePricingNormalizer
from app.schemas.pricing import NormalizedPrice, PricingUnit
from app.utils.logger import get_logger
from app.utils.region_mapper import RegionMapper

logger = get_logger(__name__)


class RDSPricingNormalizer(BasePricingNormalizer):
    """Normalizes RDS pricing data."""
    
    def get_service_name(self) -> str:
        return "rds"
    
    def normalize(self, pricing_data: Dict[str, Any], region: str) -> List[NormalizedPrice]:
        """
        Normalize RDS pricing data.
        
        Args:
            pricing_data: Raw RDS pricing data from AWS
            region: AWS region code
            
        Returns:
            List of normalized RDS prices
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
            
            product_family = product.get('productFamily', '')
            
            # Get pricing dimensions
            dimensions = self._extract_pricing_dimensions(terms)
            
            for dimension in dimensions:
                unit = dimension.get('unit', '')
                price_per_unit = float(dimension.get('pricePerUnit', {}).get('USD', 0))
                
                # Determine resource type and pricing unit
                if product_family == 'Database Instance':
                    resource_type = 'instance'
                    pricing_unit = PricingUnit.HOUR
                elif product_family == 'Database Storage':
                    resource_type = 'storage'
                    pricing_unit = PricingUnit.GB_MONTH
                elif product_family == 'System Operation':
                    resource_type = 'backup'
                    pricing_unit = PricingUnit.GB_MONTH
                else:
                    continue
                
                normalized_price = NormalizedPrice(
                    service='rds',
                    resource_type=resource_type,
                    usage_type=product_attrs.get('usagetype', ''),
                    region=region,
                    unit=pricing_unit,
                    price_per_unit=price_per_unit,
                    currency='USD',
                    attributes={
                        'instanceType': product_attrs.get('instanceType'),
                        'instanceClass': product_attrs.get('instanceClass'),
                        'databaseEngine': product_attrs.get('databaseEngine'),
                        'deploymentOption': product_attrs.get('deploymentOption'),
                        'storageType': product_attrs.get('storageType'),
                        'volumeType': product_attrs.get('volumeType'),
                        'engineCode': product_attrs.get('engineCode')
                    },
                    effective_date=datetime.utcnow(),
                    sku=sku
                )
                
                normalized_prices.append(normalized_price)
        
        logger.info(f"Normalized {len(normalized_prices)} RDS prices for region {region}")
        
        return normalized_prices
