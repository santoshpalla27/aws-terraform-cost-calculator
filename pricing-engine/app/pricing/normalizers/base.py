"""
Base normalizer interface.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.schemas.pricing import NormalizedPrice
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BasePricingNormalizer(ABC):
    """Base class for service-specific pricing normalizers."""
    
    @abstractmethod
    def get_service_name(self) -> str:
        """Get the service name this normalizer handles."""
        pass
    
    @abstractmethod
    def normalize(self, pricing_data: Dict[str, Any], region: str) -> List[NormalizedPrice]:
        """
        Normalize AWS pricing data into canonical format.
        
        Args:
            pricing_data: Raw pricing data from AWS Price List API
            region: AWS region code
            
        Returns:
            List of normalized price records
        """
        pass
    
    def _extract_sku_attributes(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract attributes from product SKU.
        
        Args:
            product: Product data from AWS pricing
            
        Returns:
            Dict of attributes
        """
        attributes = product.get('attributes', {})
        return attributes
    
    def _extract_pricing_dimensions(self, terms: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract pricing dimensions from terms.
        
        Args:
            terms: Terms data from AWS pricing
            
        Returns:
            List of pricing dimensions
        """
        dimensions = []
        
        # AWS pricing structure: terms -> OnDemand -> {offer_term_code} -> priceDimensions
        on_demand = terms.get('OnDemand', {})
        
        for offer_term in on_demand.values():
            price_dimensions = offer_term.get('priceDimensions', {})
            
            for dimension in price_dimensions.values():
                dimensions.append(dimension)
        
        return dimensions
    
    def _extract_sku_pricing_dimensions(self, terms: Dict[str, Any], sku: str) -> List[Dict[str, Any]]:
        """
        Extract pricing dimensions for a SPECIFIC SKU only.
        
        Args:
            terms: Terms data from AWS pricing
            sku: SKU to extract dimensions for
            
        Returns:
            List of pricing dimensions for this SKU only
        """
        dimensions = []
        
        # AWS pricing structure: terms -> OnDemand -> {sku}.{offer_term_code} -> priceDimensions
        on_demand = terms.get('OnDemand', {})
        
        for offer_term_code, offer_term in on_demand.items():
            # Check if this offer term belongs to the current SKU
            if not offer_term_code.startswith(sku):
                continue
            
            price_dimensions = offer_term.get('priceDimensions', {})
            
            for dimension in price_dimensions.values():
                dimensions.append(dimension)
        
        return dimensions
