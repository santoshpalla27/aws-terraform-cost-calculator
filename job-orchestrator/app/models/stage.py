"""
Stage execution models.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class StageStatus(str, Enum):
    """Stage execution status."""
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class StageExecution(BaseModel):
    """Stage execution record."""
    
    id: Optional[int] = None
    job_id: str
    stage_name: str
    
    # Execution tracking
    attempt_number: int = Field(default=1)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    
    # Status
    status: StageStatus = Field(default=StageStatus.RUNNING)
    error_message: Optional[str] = None
    
    # Metadata
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "stage_name": "PLANNING",
                "attempt_number": 1,
                "status": "RUNNING",
                "started_at": "2024-01-01T12:00:00Z"
            }
        }
