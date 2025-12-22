"""
Domain models for API Gateway.
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Job status enumeration."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Upload(BaseModel):
    """Upload domain model."""
    upload_id: str = Field(..., description="Unique upload identifier")
    user_id: str = Field(..., description="User who created the upload")
    filename: str = Field(..., description="Original filename")
    file_count: int = Field(..., description="Number of files uploaded")
    total_size: int = Field(..., description="Total size in bytes")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "upload_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "user123",
                "filename": "infrastructure.zip",
                "file_count": 5,
                "total_size": 12345,
                "created_at": "2024-01-01T12:00:00Z"
            }
        }


class Job(BaseModel):
    """Job domain model."""
    job_id: str = Field(..., description="Unique job identifier")
    upload_id: str = Field(..., description="Associated upload ID")
    user_id: str = Field(..., description="User who created the job")
    name: str = Field(..., description="Job name")
    status: JobStatus = Field(default=JobStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "650e8400-e29b-41d4-a716-446655440000",
                "upload_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "user123",
                "name": "Production Infrastructure Cost Estimate",
                "status": "PENDING",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z"
            }
        }
