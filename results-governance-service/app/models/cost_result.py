"""
Cost result domain models with IMMUTABILITY guarantees.

CRITICAL: Results are WRITE-ONCE and cannot be modified after creation.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ResourceCost(BaseModel):
    """Individual resource cost breakdown."""
    
    resource_name: str = Field(..., description="Resource identifier")
    resource_type: str = Field(..., description="AWS resource type")
    service: str = Field(..., description="AWS service")
    region: str = Field(..., description="AWS region")
    monthly_cost: Decimal = Field(..., description="Monthly cost in USD")
    unit_cost: Optional[Decimal] = Field(None, description="Unit cost")
    quantity: Optional[Decimal] = Field(None, description="Quantity")
    pricing_unit: Optional[str] = Field(None, description="Pricing unit")
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class CostResult(BaseModel):
    """
    Immutable cost estimation result.
    
    CRITICAL RULES:
    - Write-once: Created exactly once per job
    - No updates: Any modification attempt throws error
    - No deletes: Results are permanent
    - Versioned: By job_id, pricing_snapshot, usage_profile
    """
    
    # Identity
    result_id: str = Field(..., description="Unique result identifier (UUID)")
    job_id: str = Field(..., description="Associated job ID (unique)")
    
    # Versioning metadata
    pricing_snapshot: str = Field(
        ...,
        description="Pricing data version/timestamp (ISO 8601)"
    )
    usage_profile: str = Field(
        ...,
        description="Usage profile used (e.g., 'prod', 'dev')"
    )
    terraform_version: Optional[str] = Field(
        None,
        description="Terraform version used"
    )
    
    # Cost data
    total_monthly_cost: Decimal = Field(
        ...,
        description="Total estimated monthly cost"
    )
    currency: str = Field(default="USD", description="Currency code")
    breakdown: List[ResourceCost] = Field(
        default_factory=list,
        description="Per-resource cost breakdown"
    )
    
    # Confidence and metadata
    confidence: str = Field(
        default="MEDIUM",
        description="Confidence level: HIGH, MEDIUM, LOW"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    
    # Immutability markers
    is_immutable: bool = Field(
        default=True,
        description="Immutability flag (always True)"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Creation timestamp (immutable)"
    )
    created_by: Optional[str] = Field(
        None,
        description="User ID who created the result"
    )
    
    # Tracing
    correlation_id: str = Field(
        ...,
        description="Request correlation ID"
    )
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "result_id": "550e8400-e29b-41d4-a716-446655440000",
                "job_id": "650e8400-e29b-41d4-a716-446655440000",
                "pricing_snapshot": "2024-01-15T12:00:00Z",
                "usage_profile": "prod",
                "terraform_version": "1.6.0",
                "total_monthly_cost": 1234.56,
                "currency": "USD",
                "breakdown": [],
                "confidence": "HIGH",
                "is_immutable": True,
                "created_at": "2024-01-15T12:30:00Z",
                "correlation_id": "750e8400-e29b-41d4-a716-446655440000"
            }
        }


class ResultSummary(BaseModel):
    """
    Lightweight result summary for historical comparison.
    """
    
    result_id: str
    job_id: str
    total_monthly_cost: Decimal
    currency: str
    usage_profile: str
    created_at: datetime
    confidence: str
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }
