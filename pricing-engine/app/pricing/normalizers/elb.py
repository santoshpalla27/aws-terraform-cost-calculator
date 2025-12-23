"""
ELB pricing normalizer.
"""
from typing import List, Dict, Any
from datetime import datetime
from app.pricing.normalizers.base import BasePricingNormalizer
from app.schemas.pricing import NormalizedPrice, PricingUnit
from app.utils.logger import get_logger
from app.utils.region_mapper import RegionMapper

logger = get_logger(__name__)


class ELBPricingNormalizer(BasePricingNormalizer):
    """Normalizes ELB (ALB/NLB) pricing data."""
    
    def get_service_name(self) -> str:
        return "elb"
    
    def normalize(self, pricing_data: Dict[str, Any], region: str) -> List[NormalizedPrice]:
        """
        Normalize ELB pricing data.
        
        Args:
            pricing_data: Raw ELB pricing data from AWS (part of EC2 pricing)
            region: AWS region code
            
        Returns:
            List of normalized ELB prices
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
            
            # Only process Load Balancer products
            product_family = product.get('productFamily', '')
            if product_family != 'Load Balancer':
                continue
            
            usage_type = product_attrs.get('usagetype', '')
            
            # Get pricing dimensions
            dimensions = self._extract_pricing_dimensions(terms)
            
            for dimension in dimensions:
                unit = dimension.get('unit', '')
                price_per_unit = float(dimension.get('pricePerUnit', {}).get('USD', 0))
                
                # Determine resource type and pricing unit
                if 'LCUUsage' in usage_type or 'LCU' in usage_type:
                    resource_type = 'lcu'
                    pricing_unit = PricingUnit.LCU_HOUR
                elif 'LoadBalancerUsage' in usage_type:
                    resource_type = 'load_balancer'
                    pricing_unit = PricingUnit.HOUR
                else:
                    continue
                
                # Determine load balancer type
                lb_type = 'alb'  # default
                if 'network' in usage_type.lower():
                    lb_type = 'nlb'
                elif 'application' in usage_type.lower():
                    lb_type = 'alb'
                
                normalized_price = NormalizedPrice(
                    service='elb',
                    resource_type=resource_type,
                    usage_type=usage_type,
                    region=region,
                    unit=pricing_unit,
                    price_per_unit=price_per_unit,
                    currency='USD',
                    attributes={
                        'loadBalancerType': lb_type,
                        'group': product_attrs.get('group'),
                        'groupDescription': product_attrs.get('groupDescription')
                    },
                    effective_date=datetime.utcnow(),
                    sku=sku
                )
                
                normalized_prices.append(normalized_price)
        
        logger.info(f"Normalized {len(normalized_prices)} ELB prices for region {region}")
        
        return normalized_prices
