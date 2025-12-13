"""Output schema models."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime


class CostDriver(BaseModel):
    """Cost driver model."""
    component: str = Field(..., description="Cost component (compute, storage, network, other)")
    cost: Decimal = Field(..., description="Cost amount")
    percentage: float = Field(..., description="Percentage of total cost")
    description: str = Field(..., description="Description of cost driver")


class ResourceCost(BaseModel):
    """Per-resource cost breakdown."""
    
    resource_id: str = Field(..., description="Resource identifier")
    resource_type: str = Field(..., description="Resource type (aws_instance, etc.)")
    service: str = Field(..., description="AWS service (EC2, S3, etc.)")
    region: str = Field(..., description="AWS region")
    
    # Cost breakdown
    compute_cost: Decimal = Field(default=Decimal("0"), description="Compute costs")
    storage_cost: Decimal = Field(default=Decimal("0"), description="Storage costs")
    network_cost: Decimal = Field(default=Decimal("0"), description="Network costs")
    other_cost: Decimal = Field(default=Decimal("0"), description="Other costs")
    total_monthly_cost: Decimal = Field(..., description="Total monthly cost")
    
    # Metadata
    usage_profile: str = Field(..., description="Usage profile used (dev, staging, prod)")
    confidence_score: float = Field(..., description="Confidence score (0.0-1.0)")
    cost_drivers: List[CostDriver] = Field(default_factory=list, description="Top cost drivers")
    assumptions: List[Dict[str, Any]] = Field(default_factory=list, description="Cost assumptions")


class ServiceCost(BaseModel):
    """Per-service cost aggregation."""
    
    service: str = Field(..., description="AWS service name")
    total_cost: Decimal = Field(..., description="Total cost for service")
    resource_count: int = Field(..., description="Number of resources")
    resources: List[ResourceCost] = Field(default_factory=list, description="Resources in service")


class RegionCost(BaseModel):
    """Per-region cost aggregation."""
    
    region: str = Field(..., description="AWS region")
    total_cost: Decimal = Field(..., description="Total cost for region")
    resource_count: int = Field(..., description="Number of resources")
    services: Dict[str, Decimal] = Field(default_factory=dict, description="Cost by service")


class CostEstimate(BaseModel):
    """Complete cost estimate."""
    
    total_monthly_cost: Decimal = Field(..., description="Total monthly cost estimate")
    confidence_score: float = Field(..., description="Overall confidence score")
    
    # Aggregations
    by_resource: List[ResourceCost] = Field(default_factory=list, description="Per-resource costs")
    by_service: List[ServiceCost] = Field(default_factory=list, description="Per-service aggregation")
    by_region: List[RegionCost] = Field(default_factory=list, description="Per-region aggregation")
    
    # Metadata
    profile: str = Field(..., description="Usage profile used")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Estimate timestamp")
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }


class CostDiff(BaseModel):
    """Cost difference between two estimates."""
    
    total_delta: Decimal = Field(..., description="Total cost delta")
    percentage_change: float = Field(..., description="Percentage change")
    
    added_resources: List[ResourceCost] = Field(default_factory=list, description="Added resources")
    removed_resources: List[ResourceCost] = Field(default_factory=list, description="Removed resources")
    changed_resources: List[Dict[str, Any]] = Field(default_factory=list, description="Changed resources")
    
    added_cost: Decimal = Field(default=Decimal("0"), description="Cost of added resources")
    removed_cost: Decimal = Field(default=Decimal("0"), description="Cost of removed resources")
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }
