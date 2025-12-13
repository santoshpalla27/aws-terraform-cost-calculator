"""Response models."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from .domain import JobStatus


class JobResponse(BaseModel):
    """Response for job details."""
    
    job_id: str = Field(..., description="Unique job identifier")
    upload_id: str = Field(..., description="Associated upload identifier")
    status: JobStatus = Field(..., description="Current job status")
    region: str = Field(..., description="AWS region")
    created_at: datetime = Field(..., description="Job creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    result_data: Optional[Dict[str, Any]] = Field(default=None, description="Cost estimation results")
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "job_id": "job_123abc",
                "upload_id": "upload_456def",
                "status": "COMPLETED",
                "region": "us-east-1",
                "created_at": "2025-12-13T10:00:00Z",
                "updated_at": "2025-12-13T10:05:00Z",
                "error_message": None,
                "result_data": {
                    "total_monthly_cost": 1234.56,
                    "resources": []
                }
            }
        }


class JobListResponse(BaseModel):
    """Response for paginated job list."""
    
    jobs: List[JobResponse] = Field(..., description="List of jobs")
    total: int = Field(..., description="Total number of jobs")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "jobs": [],
                "total": 42,
                "page": 1,
                "page_size": 10
            }
        }


class UploadResponse(BaseModel):
    """Response for successful upload."""
    
    upload_id: str = Field(..., description="Unique upload identifier")
    project_name: str = Field(..., description="Project name")
    file_count: int = Field(..., description="Number of files uploaded")
    total_size_bytes: int = Field(..., description="Total size in bytes")
    message: str = Field(..., description="Success message")
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "upload_id": "upload_456def",
                "project_name": "my-terraform-project",
                "file_count": 5,
                "total_size_bytes": 12345,
                "message": "Files uploaded successfully"
            }
        }


class HealthCheckResponse(BaseModel):
    """Response for health check."""
    
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Current timestamp")
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2025-12-13T10:00:00Z"
            }
        }


class ErrorResponse(BaseModel):
    """Standardized error response."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid request parameters",
                "detail": {
                    "field": "region",
                    "issue": "Invalid AWS region format"
                }
            }
        }
