"""
Request models.
"""
from typing import Optional
from pydantic import BaseModel, Field


class ExecutionRequest(BaseModel):
    """Request model for Terraform execution."""
    
    job_id: str = Field(..., description="Unique job identifier")
    workspace_reference: str = Field(..., description="Storage reference to Terraform files")
    credential_reference: Optional[str] = Field(
        None,
        description="Credential reference (e.g., 'assume-role:terraform-readonly')"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "workspace_reference": "s3://bucket/uploads/550e8400.zip",
                "credential_reference": "assume-role:terraform-readonly"
            }
        }
