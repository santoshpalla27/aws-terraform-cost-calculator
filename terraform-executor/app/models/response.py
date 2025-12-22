"""
Response models.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ErrorType(str, Enum):
    """Error type enumeration."""
    VALIDATION_ERROR = "validation_error"
    PROVIDER_ERROR = "provider_error"
    EXECUTION_TIMEOUT = "execution_timeout"
    SECURITY_VIOLATION = "security_violation"
    RESOURCE_LIMIT = "resource_limit"
    UNKNOWN_ERROR = "unknown_error"


class ExecutionError(BaseModel):
    """Execution error details."""
    type: ErrorType
    message: str
    details: Optional[Dict[str, Any]] = None


class ExecutionMetadata(BaseModel):
    """Execution metadata."""
    duration_ms: int
    cpu_usage: Optional[float] = None
    memory_mb: Optional[int] = None


class ExecutionResponse(BaseModel):
    """Response model for Terraform execution."""
    success: bool
    job_id: str
    plan_reference: Optional[str] = Field(None, description="Storage reference to plan.json")
    metadata: Optional[ExecutionMetadata] = None
    error: Optional[ExecutionError] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "plan_reference": "s3://bucket/plans/550e8400.json",
                "metadata": {
                    "duration_ms": 12345,
                    "cpu_usage": 1.5,
                    "memory_mb": 512
                }
            }
        }
