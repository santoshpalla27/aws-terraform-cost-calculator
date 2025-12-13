"""Domain models and enums."""

from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Job execution status."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"


class Job(BaseModel):
    """Internal job representation."""
    
    job_id: str = Field(..., description="Unique job identifier")
    upload_id: str = Field(..., description="Associated upload identifier")
    status: JobStatus = Field(default=JobStatus.PENDING, description="Current job status")
    region: str = Field(..., description="AWS region for cost estimation")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Job creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    result_data: Optional[Dict[str, Any]] = Field(default=None, description="Cost estimation results")
    idempotency_key: Optional[str] = Field(default=None, description="Idempotency key for duplicate prevention")
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "job_id": "job_123abc",
                "upload_id": "upload_456def",
                "status": "PENDING",
                "region": "us-east-1",
                "created_at": "2025-12-13T10:00:00Z",
                "updated_at": "2025-12-13T10:00:00Z",
            }
        }


class UploadedFile(BaseModel):
    """Uploaded file metadata."""
    
    upload_id: str = Field(..., description="Unique upload identifier")
    project_name: str = Field(..., description="Project name")
    file_count: int = Field(..., description="Number of Terraform files")
    total_size_bytes: int = Field(..., description="Total size in bytes")
    upload_path: str = Field(..., description="Storage path")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Upload timestamp")
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "upload_id": "upload_456def",
                "project_name": "my-terraform-project",
                "file_count": 5,
                "total_size_bytes": 12345,
                "upload_path": "/app/uploads/upload_456def",
                "created_at": "2025-12-13T10:00:00Z",
            }
        }
