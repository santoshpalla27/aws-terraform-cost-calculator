"""
Execution state models for async Terraform execution.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class ExecutionStatus(str, Enum):
    """Execution status enumeration."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    KILLED = "KILLED"


class TerraformExecutionRequest(BaseModel):
    """Request to execute Terraform."""
    job_id: str = Field(..., description="Job ID for correlation")
    terraform_source: str = Field(..., description="Terraform source code or reference")
    variables: Optional[Dict[str, Any]] = Field(None, description="Terraform variables")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "terraform_source": "resource \"aws_instance\" \"example\" { ... }",
                "variables": {"region": "us-east-1"}
            }
        }


class TerraformExecutionResponse(BaseModel):
    """Response from execution submission."""
    execution_id: str = Field(..., description="Unique execution identifier")
    job_id: str = Field(..., description="Job ID for correlation")
    status: ExecutionStatus = Field(..., description="Current execution status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "execution_id": "exec_abc123",
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "PENDING"
            }
        }


class ExecutionStatusResponse(BaseModel):
    """Execution status response."""
    execution_id: str
    job_id: str
    status: ExecutionStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None


class ExecutionResultResponse(BaseModel):
    """Execution result response."""
    execution_id: str
    job_id: str
    status: ExecutionStatus
    plan_json: Optional[Dict[str, Any]] = Field(None, description="Terraform plan JSON output")
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
