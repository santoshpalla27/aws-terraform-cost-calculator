"""Request models."""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class CreateJobRequest(BaseModel):
    """Request to create a new cost estimation job."""
    
    upload_id: str = Field(..., description="Upload identifier from previous upload", min_length=1)
    region: str = Field(default="us-east-1", description="AWS region for cost estimation")
    idempotency_key: Optional[str] = Field(
        default=None,
        description="Optional idempotency key to prevent duplicate job creation"
    )
    
    @field_validator("region")
    @classmethod
    def validate_region(cls, v: str) -> str:
        """Validate AWS region format."""
        if not v or len(v) < 3:
            raise ValueError("Invalid AWS region")
        return v
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "upload_id": "upload_456def",
                "region": "us-east-1",
                "idempotency_key": "unique-key-123"
            }
        }


class UploadMetadata(BaseModel):
    """Metadata for Terraform file upload."""
    
    project_name: str = Field(..., description="Project name", min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, description="Optional project description", max_length=500)
    
    @field_validator("project_name")
    @classmethod
    def validate_project_name(cls, v: str) -> str:
        """Validate project name contains only safe characters."""
        if not v.replace("-", "").replace("_", "").replace(" ", "").isalnum():
            raise ValueError("Project name can only contain alphanumeric characters, hyphens, underscores, and spaces")
        return v
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "project_name": "my-terraform-project",
                "description": "Production infrastructure for web application"
            }
        }
