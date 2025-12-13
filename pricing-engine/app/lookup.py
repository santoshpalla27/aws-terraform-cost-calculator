"""Pricing lookup service."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .database import get_db
from .models import Service, Product, PricingDimension
from .units import convert_to_hourly

logger = logging.getLogger(__name__)


class PricingLookup:
    """Deterministic pricing lookup service."""
    
    def lookup_price(
        self,
        service_code: str,
        region: str,
        attributes: Dict[str, Any],
        term_type: str = "OnDemand"
    ) -> Optional[Dict[str, Any]]:
        """Lookup pricing for a resource.
        
        Args:
            service_code: AWS service code (e.g., AmazonEC2)
            region: AWS region (e.g., us-east-1)
            attributes: Product attributes for matching
            term_type: Pricing term type (OnDemand, Reserved, etc.)
            
        Returns:
            Pricing information or None
        """
        with get_db() as db:
            # Find service
            service = db.query(Service).filter_by(service_code=service_code).first()
            if not service:
                logger.warning(f"Service not found: {service_code}")
                return None
            
            # Find product by attributes
            product = self._find_product(db, service.id, region, attributes)
            if not product:
                logger.warning(f"Product not found for {service_code} in {region}")
                return None
            
            # Get pricing dimension
            pricing = db.query(PricingDimension).filter(
                and_(
                    PricingDimension.product_id == product.id,
                    PricingDimension.term_type == term_type,
                    PricingDimension.effective_date <= datetime.now()
                )
            ).order_by(PricingDimension.effective_date.desc()).first()
            
            if not pricing:
                logger.warning(f"Pricing not found for SKU {product.sku}")
                return None
            
            return {
                "sku": product.sku,
                "product_family": product.product_family,
                "region": product.region,
                "unit": pricing.unit,
                "price_per_unit": float(pricing.price_per_unit),
                "currency": pricing.currency,
                "term_type": pricing.term_type,
                "description": pricing.description,
                "effective_date": pricing.effective_date.isoformat()
            }
    
    def _find_product(
        self,
        db: Session,
        service_id: int,
        region: str,
        attributes: Dict[str, Any]
    ) -> Optional[Product]:
        """Find product by attributes.
        
        Args:
            db: Database session
            service_id: Service ID
            region: Region
            attributes: Attributes to match
            
        Returns:
            Product or None
        """
        # Query products
        products = db.query(Product).filter(
            and_(
                Product.service_id == service_id,
                Product.region == region
            )
        ).all()
        
        # Match attributes
        for product in products:
            if self._attributes_match(product.attributes, attributes):
                return product
        
        return None
    
    def _attributes_match(self, product_attrs: Dict[str, Any], search_attrs: Dict[str, Any]) -> bool:
        """Check if product attributes match search criteria.
        
        Args:
            product_attrs: Product attributes
            search_attrs: Search attributes
            
        Returns:
            True if match
        """
        for key, value in search_attrs.items():
            if key not in product_attrs:
                return False
            if product_attrs[key] != value:
                return False
        return True
