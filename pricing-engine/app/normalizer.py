"""Pricing data normalization."""

import logging
from typing import Dict, Any, List, Tuple
from decimal import Decimal
from datetime import datetime

from .units import normalize_unit
from .price_list_client import PriceListClient

logger = logging.getLogger(__name__)


class PricingNormalizer:
    """Normalizes pricing data from AWS Price List API."""
    
    def __init__(self):
        """Initialize normalizer."""
        self.client = PriceListClient()
        self.region_index = self.client.get_region_index()
    
    def normalize_offer(self, service_code: str, offer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize offer data.
        
        Args:
            service_code: Service code
            offer_data: Raw offer data
            
        Returns:
            Normalized data with products and pricing
        """
        products = []
        pricing_dimensions = []
        
        # Parse products
        for sku, product_data in offer_data.get("products", {}).items():
            normalized_product = self._normalize_product(sku, product_data)
            products.append(normalized_product)
        
        # Parse pricing terms
        for term_type, terms in offer_data.get("terms", {}).items():
            for sku, sku_terms in terms.items():
                for rate_code, rate_data in sku_terms.items():
                    for dimension_key, dimension_data in rate_data.get("priceDimensions", {}).items():
                        normalized_dimension = self._normalize_pricing_dimension(
                            sku, term_type, dimension_key, dimension_data
                        )
                        pricing_dimensions.append(normalized_dimension)
        
        return {
            "service_code": service_code,
            "version": offer_data.get("version"),
            "publication_date": offer_data.get("publicationDate"),
            "products": products,
            "pricing_dimensions": pricing_dimensions
        }
    
    def _normalize_product(self, sku: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize product data.
        
        Args:
            sku: Product SKU
            product_data: Raw product data
            
        Returns:
            Normalized product
        """
        attributes = product_data.get("attributes", {})
        location = attributes.get("location", "")
        
        # Map location to region
        region = self.region_index.get(location)
        
        return {
            "sku": sku,
            "product_family": product_data.get("productFamily"),
            "attributes": attributes,
            "region": region,
            "location": location
        }
    
    def _normalize_pricing_dimension(
        self,
        sku: str,
        term_type: str,
        rate_code: str,
        dimension_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Normalize pricing dimension.
        
        Args:
            sku: Product SKU
            term_type: Term type (OnDemand, Reserved, etc.)
            rate_code: Rate code
            dimension_data: Raw dimension data
            
        Returns:
            Normalized pricing dimension
        """
        # Extract price
        price_per_unit_data = dimension_data.get("pricePerUnit", {})
        price_usd = price_per_unit_data.get("USD", "0")
        
        # Parse unit
        unit = dimension_data.get("unit", "")
        normalized_unit = normalize_unit(unit)
        
        # Parse range (for tiered pricing)
        begin_range = dimension_data.get("beginRange")
        end_range = dimension_data.get("endRange")
        
        # Convert to Decimal
        try:
            price_decimal = Decimal(price_usd)
        except:
            price_decimal = Decimal("0")
        
        return {
            "sku": sku,
            "rate_code": rate_code,
            "description": dimension_data.get("description", ""),
            "unit": normalized_unit,
            "original_unit": unit,
            "price_per_unit": price_decimal,
            "begin_range": Decimal(begin_range) if begin_range else None,
            "end_range": Decimal(end_range) if end_range != "Inf" and end_range else None,
            "term_type": term_type
        }
