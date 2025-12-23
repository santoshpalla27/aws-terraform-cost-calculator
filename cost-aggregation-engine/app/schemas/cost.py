"""
Cost schemas and models.
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from decimal import Decimal
from enum import Enum


class ConfidenceLevel(str, Enum):
    """Confidence level for cost calculations."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class CostDimension(BaseModel):
    """Single dimension cost calculation."""
    
    dimension: str = Field(..., description="Pricing dimension (e.g., 'instance_hours', 'storage_gb')")
    usage_units: Decimal = Field(..., description="Usage units")
    unit_price: Decimal = Field(..., description="Unit price")
    cost: Decimal = Field(..., description="Calculated cost (usage × price)")
    unit: str = Field(..., description="Unit (hours, GB-Month, etc.)")
    currency: str = Field(default="USD", description="Currency")
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }
        json_schema_extra = {
            "example": {
                "dimension": "instance_hours",
                "usage_units": "730.0",
                "unit_price": "0.0104",
                "cost": "7.592",
                "unit": "hours",
                "currency": "USD"
            }
        }


class CostScenario(BaseModel):
    """Cost scenario (min/expected/max)."""
    
    min: Decimal = Field(..., description="Minimum cost")
    expected: Decimal = Field(..., description="Expected cost")
    max: Decimal = Field(..., description="Maximum cost")
    currency: str = Field(default="USD", description="Currency")
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }
        json_schema_extra = {
            "example": {
                "min": "5.0",
                "expected": "7.592",
                "max": "10.0",
                "currency": "USD"
            }
        }


class CostDiff(BaseModel):
    """Cost differences and spreads."""
    
    expected_minus_min: Decimal = Field(..., description="Expected - Min")
    max_minus_expected: Decimal = Field(..., description="Max - Expected")
    max_minus_min: Decimal = Field(..., description="Max - Min")
    expected_minus_min_pct: Decimal = Field(..., description="(Expected - Min) / Min × 100")
    max_minus_expected_pct: Decimal = Field(..., description="(Max - Expected) / Expected × 100")
    scenario_spread: Decimal = Field(..., description="(Max - Min) / Expected")
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class ResourceCost(BaseModel):
    """Per-resource cost breakdown."""
    
    resource_id: str
    resource_type: str
    service: str
    region: str
    dimensions: List[CostDimension] = Field(default_factory=list, description="Cost per dimension")
    scenario: CostScenario
    diff: CostDiff
    confidence: ConfidenceLevel
    confidence_sources: Dict[str, str] = Field(
        default_factory=dict,
        description="Confidence sources (pricing, usage, metadata)"
    )
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class AggregatedCost(BaseModel):
    """Aggregated costs by grouping."""
    
    group_by: str = Field(..., description="Grouping key (service, region, stack)")
    group_value: str = Field(..., description="Group value (e.g., 'ec2', 'us-east-1')")
    scenario: CostScenario
    diff: CostDiff
    resource_count: int = Field(..., description="Number of resources in group")
    confidence: ConfidenceLevel
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class FCM(BaseModel):
    """Final Cost Model."""
    
    resource_costs: List[ResourceCost] = Field(
        default_factory=list,
        description="Per-resource costs"
    )
    aggregated_by_service: List[AggregatedCost] = Field(
        default_factory=list,
        description="Costs aggregated by service"
    )
    aggregated_by_region: List[AggregatedCost] = Field(
        default_factory=list,
        description="Costs aggregated by region"
    )
    total_cost: CostScenario = Field(..., description="Total stack cost")
    total_diff: CostDiff = Field(..., description="Total cost diffs")
    overall_confidence: ConfidenceLevel = Field(..., description="Overall confidence")
    determinism_hash: Optional[str] = Field(None, description="Hash for determinism verification")
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class AggregateRequest(BaseModel):
    """Request to aggregate costs."""
    
    resources: List[Dict[str, Any]] = Field(..., description="Resources from ERG")
    pricing_records: List[Dict[str, Any]] = Field(..., description="Pricing records")
    usage_records: List[Dict[str, Any]] = Field(..., description="Usage records from UARG")
    
    class Config:
        json_schema_extra = {
            "example": {
                "resources": [],
                "pricing_records": [],
                "usage_records": []
            }
        }


class AggregateResponse(BaseModel):
    """Response from cost aggregation."""
    
    fcm: FCM = Field(..., description="Final Cost Model")
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }
