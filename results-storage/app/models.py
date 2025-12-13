"""Database models."""

from sqlalchemy import Column, Integer, String, DECIMAL, TIMESTAMP, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

Base = declarative_base()


class Job(Base):
    """Cost estimation job."""
    
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True)
    job_id = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, index=True)
    
    # Job metadata
    profile = Column(String(50), nullable=False)
    terraform_plan_hash = Column(String(64))
    user_id = Column(String(100), index=True)
    
    # Status
    status = Column(String(20), default="completed", index=True)
    
    # Results summary
    total_monthly_cost = Column(DECIMAL(20, 2))
    confidence_score = Column(DECIMAL(3, 2))
    resource_count = Column(Integer)
    
    # Schema version
    schema_version = Column(Integer, default=1)
    
    # Relationships
    cost_results = relationship("CostResult", back_populates="job", cascade="all, delete-orphan")
    service_costs = relationship("ServiceCost", back_populates="job", cascade="all, delete-orphan")
    region_costs = relationship("RegionCost", back_populates="job", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Job(job_id={self.job_id}, profile={self.profile}, cost={self.total_monthly_cost})>"


class CostResult(Base):
    """Immutable cost result record."""
    
    __tablename__ = "cost_results"
    
    id = Column(Integer, primary_key=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.job_id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # Resource identification
    resource_id = Column(String(255), nullable=False)
    resource_type = Column(String(100), nullable=False)
    service = Column(String(50), nullable=False, index=True)
    region = Column(String(50), nullable=False, index=True)
    
    # Cost breakdown
    compute_cost = Column(DECIMAL(20, 10), default=0)
    storage_cost = Column(DECIMAL(20, 10), default=0)
    network_cost = Column(DECIMAL(20, 10), default=0)
    other_cost = Column(DECIMAL(20, 10), default=0)
    total_monthly_cost = Column(DECIMAL(20, 10), nullable=False, index=True)
    
    # Metadata
    confidence_score = Column(DECIMAL(3, 2))
    usage_profile = Column(String(50))
    cost_drivers = Column(JSONB)
    assumptions = Column(JSONB)
    
    # Relationships
    job = relationship("Job", back_populates="cost_results")
    
    def __repr__(self):
        return f"<CostResult(resource_id={self.resource_id}, cost={self.total_monthly_cost})>"


class ServiceCost(Base):
    """Service cost aggregation (denormalized)."""
    
    __tablename__ = "service_costs"
    
    id = Column(Integer, primary_key=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.job_id", ondelete="CASCADE"), nullable=False, index=True)
    service = Column(String(50), nullable=False, index=True)
    total_cost = Column(DECIMAL(20, 2), nullable=False)
    resource_count = Column(Integer, nullable=False)
    
    # Relationships
    job = relationship("Job", back_populates="service_costs")
    
    def __repr__(self):
        return f"<ServiceCost(service={self.service}, cost={self.total_cost})>"


class RegionCost(Base):
    """Region cost aggregation (denormalized)."""
    
    __tablename__ = "region_costs"
    
    id = Column(Integer, primary_key=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.job_id", ondelete="CASCADE"), nullable=False, index=True)
    region = Column(String(50), nullable=False, index=True)
    total_cost = Column(DECIMAL(20, 2), nullable=False)
    resource_count = Column(Integer, nullable=False)
    services = Column(JSONB)
    
    # Relationships
    job = relationship("Job", back_populates="region_costs")
    
    def __repr__(self):
        return f"<RegionCost(region={self.region}, cost={self.total_cost})>"
