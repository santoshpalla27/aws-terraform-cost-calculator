"""Data models."""

from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ExecutionStatus(str, Enum):
    """Execution status."""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"


class ExecutionRequest(BaseModel):
    """Request to execute Terraform."""
    
    job_id: str = Field(..., description="Job identifier")
    upload_id: str = Field(..., description="Upload identifier")
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "job_id": "job_123abc",
                "upload_id": "upload_456def"
            }
        }


class ExecutionResponse(BaseModel):
    """Response from Terraform execution."""
    
    job_id: str = Field(..., description="Job identifier")
    status: ExecutionStatus = Field(..., description="Execution status")
    plan_json: Optional[Dict[str, Any]] = Field(default=None, description="Terraform plan JSON")
    error_type: Optional[str] = Field(default=None, description="Error type if failed")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    terraform_output: Optional[str] = Field(default=None, description="Raw Terraform output")
    execution_time_seconds: Optional[float] = Field(default=None, description="Execution time")
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "job_id": "job_123abc",
                "status": "SUCCESS",
                "plan_json": {
                    "format_version": "1.2",
                    "terraform_version": "1.6.6",
                    "planned_values": {}
                },
                "execution_time_seconds": 12.5
            }
        }


class HealthCheckResponse(BaseModel):
    """Health check response."""
    
    status: str = Field(..., description="Service status")
    terraform_version: Optional[str] = Field(default=None, description="Terraform version")
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "terraform_version": "1.6.6"
            }
        }
