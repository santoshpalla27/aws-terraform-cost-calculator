"""
Job domain models.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from app.state_machine.states import JobState


class Job(BaseModel):
    """Job domain model."""
    
    job_id: str = Field(..., description="Unique job identifier")
    upload_id: str = Field(..., description="Associated upload ID")
    user_id: str = Field(..., description="User who created the job")
    name: str = Field(..., description="Job name")
    
    # State machine
    current_state: JobState = Field(default=JobState.UPLOADED)
    previous_state: Optional[JobState] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Execution tracking
    retry_count: int = Field(default=0)
    error_message: Optional[str] = None
    
    # Results
    plan_reference: Optional[str] = None
    result_reference: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "upload_id": "650e8400-e29b-41d4-a716-446655440000",
                "user_id": "user123",
                "name": "Production Infrastructure Cost Estimate",
                "current_state": "UPLOADED",
                "created_at": "2024-01-01T12:00:00Z"
            }
        }


class JobStateResponse(BaseModel):
    """Response model for job state query."""
    
    job_id: str
    current_state: JobState
    previous_state: Optional[JobState]
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "current_state": "PLANNING",
                "previous_state": "UPLOADED",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:01:00Z"
            }
        }
