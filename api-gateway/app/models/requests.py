"""
Pydantic request models.
"""
from typing import Optional
from pydantic import BaseModel, Field


class CreateJobRequest(BaseModel):
    """Request model for creating a job."""
    upload_id: str = Field(..., description="Upload ID to create job from")
    name: str = Field(..., min_length=1, max_length=255, description="Job name")
    usage_profile_id: Optional[str] = Field(None, description="Usage profile ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "upload_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Production Infrastructure Cost Estimate",
                "usage_profile_id": "default"
            }
        }


class AuthTokenRequest(BaseModel):
    """Request model for authentication token."""
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "user@example.com",
                "password": "secure-password"
            }
        }
