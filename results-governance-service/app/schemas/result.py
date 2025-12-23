"""
Result schemas for API.
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID


class StoreResultRequest(BaseModel):
    """Request to store a cost result."""
    
    project_id: str = Field(..., description="Project identifier")
    environment: str = Field(..., description="Environment (dev/stage/prod)")
    fcm: Dict[str, Any] = Field(..., description="Final Cost Model")
    git_commit: Optional[str] = Field(None, description="Git commit hash")
    build_id: Optional[str] = Field(None, description="Build ID")
    trigger: Optional[str] = Field(None, description="Trigger type (manual/ci/scheduled)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "my-terraform-project",
                "environment": "prod",
                "fcm": {},
                "git_commit": "abc123",
                "build_id": "build-456",
                "trigger": "ci"
            }
        }


class StoreResultResponse(BaseModel):
    """Response from storing a result."""
    
    result_id: UUID = Field(..., description="Unique result ID")
    determinism_hash: str = Field(..., description="Determinism hash")
    timestamp: datetime = Field(..., description="Storage timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "result_id": "550e8400-e29b-41d4-a716-446655440000",
                "determinism_hash": "abc123def456",
                "timestamp": "2025-12-23T11:30:00Z"
            }
        }


class ResultDetail(BaseModel):
    """Detailed result information."""
    
    result_id: UUID
    project_id: str
    environment: str
    timestamp: datetime
    fcm: Dict[str, Any]
    determinism_hash: str
    overall_confidence: str
    git_commit: Optional[str]
    build_id: Optional[str]
    trigger: Optional[str]
    
    class Config:
        from_attributes = True


class HistoryQuery(BaseModel):
    """Query for historical results."""
    
    project_id: str = Field(..., description="Project ID")
    environment: Optional[str] = Field(None, description="Environment filter")
    start_date: Optional[datetime] = Field(None, description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")
    limit: int = Field(default=100, description="Result limit")
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "my-terraform-project",
                "environment": "prod",
                "limit": 50
            }
        }


class HistoryResponse(BaseModel):
    """Response with historical results."""
    
    results: List[ResultDetail] = Field(default_factory=list)
    count: int = Field(..., description="Total count")
    
    class Config:
        json_schema_extra = {
            "example": {
                "results": [],
                "count": 0
            }
        }
