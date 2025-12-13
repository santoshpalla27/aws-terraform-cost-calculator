"""Database models."""

from sqlalchemy import Column, Integer, String, Text, DECIMAL, TIMESTAMP, ForeignKey, Date, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

Base = declarative_base()


class Service(Base):
    """AWS service model."""
    
    __tablename__ = "services"
    
    id = Column(Integer, primary_key=True)
    service_code = Column(String(100), unique=True, nullable=False, index=True)
    service_name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    products = relationship("Product", back_populates="service", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Service(code={self.service_code}, name={self.service_name})>"


class Product(Base):
    """Product (SKU) model."""
    
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="CASCADE"), nullable=False, index=True)
    sku = Column(String(100), unique=True, nullable=False, index=True)
    product_family = Column(String(100), index=True)
    attributes = Column(JSONB, nullable=False, default={})
    region = Column(String(50), index=True)
    location = Column(String(255))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    service = relationship("Service", back_populates="products")
    pricing_dimensions = relationship("PricingDimension", back_populates="product", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Product(sku={self.sku}, family={self.product_family})>"


class PricingDimension(Base):
    """Pricing dimension model."""
    
    __tablename__ = "pricing_dimensions"
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    rate_code = Column(String(100), nullable=False)
    description = Column(Text)
    unit = Column(String(50), nullable=False, index=True)
    price_per_unit = Column(DECIMAL(20, 10), nullable=False)
    begin_range = Column(DECIMAL(20, 2))
    end_range = Column(DECIMAL(20, 2))
    currency = Column(String(10), default="USD")
    term_type = Column(String(50), default="OnDemand", index=True)
    effective_date = Column(TIMESTAMP, nullable=False, index=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="pricing_dimensions")
    
    def __repr__(self):
        return f"<PricingDimension(rate_code={self.rate_code}, price={self.price_per_unit} {self.currency}/{self.unit})>"


class PricingSnapshot(Base):
    """Pricing snapshot model."""
    
    __tablename__ = "pricing_snapshots"
    
    id = Column(Integer, primary_key=True)
    snapshot_date = Column(Date, unique=True, nullable=False, index=True)
    version = Column(String(50), nullable=False)
    services_count = Column(Integer, default=0)
    products_count = Column(Integer, default=0)
    pricing_count = Column(Integer, default=0)
    status = Column(String(20), default="active", index=True)
    metadata = Column(JSONB, default={})
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    completed_at = Column(TIMESTAMP)
    
    def __repr__(self):
        return f"<PricingSnapshot(date={self.snapshot_date}, status={self.status})>"
