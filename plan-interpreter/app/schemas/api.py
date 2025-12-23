"""
Request/Response models for Plan Interpreter API.
"""
from pydantic import BaseModel, Field
from app.schemas.nrg import NormalizedResourceGraph


class InterpretRequest(BaseModel):
    """Request to interpret a Terraform plan."""
    
    plan_json_reference: str = Field(..., description="Storage reference to plan.json")
    
    class Config:
        json_schema_extra = {
            "example": {
                "plan_json_reference": "s3://bucket/plans/550e8400.json"
            }
        }


class InterpretResponse(BaseModel):
    """Response from plan interpretation."""
    
    normalized_resource_graph: list  # List of NRGNode
    interpretation_metadata: dict  # InterpretationMetadata
    
    class Config:
        json_schema_extra = {
            "example": {
                "normalized_resource_graph": [],
                "interpretation_metadata": {
                    "plan_hash": "abc123",
                    "total_resources": 0,
                    "resources_by_type": {},
                    "unknown_value_count": 0,
                    "module_depth": 0,
                    "interpretation_timestamp": "2024-01-15T10:30:00Z"
                }
            }
        }

