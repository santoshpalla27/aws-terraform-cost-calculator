"""
Pydantic response models.
"""
from typing import Optional, List, Generic, TypeVar, Any
from pydantic import BaseModel, Field
from app.models.domain import Upload, Job

T = TypeVar('T')


class ErrorDetail(BaseModel):
    """Error detail model."""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Any] = Field(None, description="Additional error details")


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: ErrorDetail
    correlation_id: Optional[str] = Field(None, description="Request correlation ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid request",
                    "details": {"field": "upload_id", "issue": "required"}
                },
                "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class UploadResponse(BaseModel):
    """Response model for upload operations."""
    upload: Upload
    message: str = Field(default="Upload successful")
    
    class Config:
        json_schema_extra = {
            "example": {
                "upload": {
                    "upload_id": "550e8400-e29b-41d4-a716-446655440000",
                    "user_id": "user123",
                    "filename": "infrastructure.zip",
                    "file_count": 5,
                    "total_size": 12345,
                    "created_at": "2024-01-01T12:00:00Z"
                },
                "message": "Upload successful"
            }
        }


class JobResponse(BaseModel):
    """Response model for job operations."""
    job: Job
    message: str = Field(default="Job created successfully")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job": {
                    "job_id": "650e8400-e29b-41d4-a716-446655440000",
                    "upload_id": "550e8400-e29b-41d4-a716-446655440000",
                    "user_id": "user123",
                    "name": "Production Infrastructure Cost Estimate",
                    "status": "PENDING",
                    "created_at": "2024-01-01T12:00:00Z",
                    "updated_at": "2024-01-01T12:00:00Z"
                },
                "message": "Job created successfully"
            }
        }


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""
    data: List[T]
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")


class AuthTokenResponse(BaseModel):
    """Response model for authentication token."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token expiration in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(default="healthy")
    timestamp: str
    service: str = Field(default="api-gateway")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-01T12:00:00Z",
                "service": "api-gateway"
            }
        }
