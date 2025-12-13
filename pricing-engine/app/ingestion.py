"""Pricing ingestion service."""

import logging
from typing import List, Dict, Any
from datetime import datetime, date
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import Service, Product, PricingDimension, PricingSnapshot
from .price_list_client import PriceListClient
from .normalizer import PricingNormalizer

logger = logging.getLogger(__name__)


class PricingIngestion:
    """Pricing ingestion workflow."""
    
    def __init__(self):
        """Initialize ingestion service."""
        self.client = PriceListClient()
        self.normalizer = PricingNormalizer()
    
    def ingest_all_services(self) -> PricingSnapshot:
        """Ingest pricing for all target services.
        
        Returns:
            Pricing snapshot
        """
        logger.info(f"Starting ingestion for {len(settings.target_services)} services")
        
        # Create snapshot
        with get_db() as db:
            snapshot = PricingSnapshot(
                snapshot_date=date.today(),
                version=datetime.now().strftime("%Y%m%d%H%M%S"),
                status="in_progress"
            )
            db.add(snapshot)
            db.flush()
            snapshot_id = snapshot.id
        
        total_products = 0
        total_pricing = 0
        
        # Ingest each service
        for service_code in settings.target_services:
            try:
                products_count, pricing_count = self.ingest_service(service_code)
                total_products += products_count
                total_pricing += pricing_count
                logger.info(f"Ingested {service_code}: {products_count} products, {pricing_count} pricing dimensions")
            except Exception as e:
                logger.error(f"Failed to ingest {service_code}: {e}")
        
        # Update snapshot
        with get_db() as db:
            snapshot = db.query(PricingSnapshot).filter_by(id=snapshot_id).first()
            snapshot.services_count = len(settings.target_services)
            snapshot.products_count = total_products
            snapshot.pricing_count = total_pricing
            snapshot.status = "active"
            snapshot.completed_at = datetime.now()
        
        logger.info(f"Ingestion complete: {total_products} products, {total_pricing} pricing dimensions")
        
        return snapshot
    
    def ingest_service(self, service_code: str) -> tuple[int, int]:
        """Ingest pricing for a single service.
        
        Args:
            service_code: Service code (e.g., AmazonEC2)
            
        Returns:
            Tuple of (products_count, pricing_count)
        """
        logger.info(f"Ingesting {service_code}")
        
        # Fetch offer data
        offer_data = self.client.get_service_offer(service_code)
        if not offer_data:
            logger.warning(f"No offer data for {service_code}")
            return 0, 0
        
        # Normalize data
        normalized = self.normalizer.normalize_offer(service_code, offer_data)
        
        # Insert into database
        with get_db() as db:
            # Insert or get service
            service = db.query(Service).filter_by(service_code=service_code).first()
            if not service:
                service = Service(
                    service_code=service_code,
                    service_name=offer_data.get("offerCode", service_code)
                )
                db.add(service)
                db.flush()
            
            service_id = service.id
            
            # Batch insert products
            products_count = self._insert_products(db, service_id, normalized["products"])
            
            # Batch insert pricing dimensions
            pricing_count = self._insert_pricing_dimensions(db, normalized["pricing_dimensions"])
        
        return products_count, pricing_count
    
    def _insert_products(self, db: Session, service_id: int, products: List[Dict[str, Any]]) -> int:
        """Batch insert products.
        
        Args:
            db: Database session
            service_id: Service ID
            products: List of normalized products
            
        Returns:
            Number of products inserted
        """
        count = 0
        batch = []
        
        for product_data in products:
            # Check if product exists
            existing = db.query(Product).filter_by(sku=product_data["sku"]).first()
            if existing:
                continue
            
            product = Product(
                service_id=service_id,
                sku=product_data["sku"],
                product_family=product_data.get("product_family"),
                attributes=product_data.get("attributes", {}),
                region=product_data.get("region"),
                location=product_data.get("location")
            )
            batch.append(product)
            count += 1
            
            # Batch insert
            if len(batch) >= settings.batch_size:
                db.bulk_save_objects(batch)
                db.flush()
                batch = []
        
        # Insert remaining
        if batch:
            db.bulk_save_objects(batch)
            db.flush()
        
        return count
    
    def _insert_pricing_dimensions(self, db: Session, pricing_dimensions: List[Dict[str, Any]]) -> int:
        """Batch insert pricing dimensions.
        
        Args:
            db: Database session
            pricing_dimensions: List of normalized pricing dimensions
            
        Returns:
            Number of pricing dimensions inserted
        """
        count = 0
        batch = []
        effective_date = datetime.now()
        
        for dimension_data in pricing_dimensions:
            # Get product ID
            product = db.query(Product).filter_by(sku=dimension_data["sku"]).first()
            if not product:
                continue
            
            dimension = PricingDimension(
                product_id=product.id,
                rate_code=dimension_data["rate_code"],
                description=dimension_data.get("description"),
                unit=dimension_data["unit"],
                price_per_unit=dimension_data["price_per_unit"],
                begin_range=dimension_data.get("begin_range"),
                end_range=dimension_data.get("end_range"),
                term_type=dimension_data.get("term_type", "OnDemand"),
                effective_date=effective_date
            )
            batch.append(dimension)
            count += 1
            
            # Batch insert
            if len(batch) >= settings.batch_size:
                db.bulk_save_objects(batch)
                db.flush()
                batch = []
        
        # Insert remaining
        if batch:
            db.bulk_save_objects(batch)
            db.flush()
        
        return count
