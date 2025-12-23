"""
Comparison schemas for API.
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from decimal import Decimal
from uuid import UUID


class CompareRequest(BaseModel):
    """Request to compare two results."""
    
    result_id_1: UUID = Field(..., description="First result ID")
    result_id_2: UUID = Field(..., description="Second result ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "result_id_1": "550e8400-e29b-41d4-a716-446655440000",
                "result_id_2": "550e8400-e29b-41d4-a716-446655440001"
            }
        }


class CostDelta(BaseModel):
    """Cost delta between two results."""
    
    absolute: Decimal = Field(..., description="Absolute difference")
    percentage: Decimal = Field(..., description="Percentage difference")
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class CompareResponse(BaseModel):
    """Response from comparison."""
    
    result_1: Dict[str, Any] = Field(..., description="First result summary")
    result_2: Dict[str, Any] = Field(..., description="Second result summary")
    
    delta_min: CostDelta = Field(..., description="Delta for min scenario")
    delta_expected: CostDelta = Field(..., description="Delta for expected scenario")
    delta_max: CostDelta = Field(..., description="Delta for max scenario")
    
    service_deltas: Dict[str, CostDelta] = Field(
        default_factory=dict,
        description="Deltas by service"
    )
    region_deltas: Dict[str, CostDelta] = Field(
        default_factory=dict,
        description="Deltas by region"
    )
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }
