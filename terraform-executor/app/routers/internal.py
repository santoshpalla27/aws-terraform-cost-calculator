"""
Internal API endpoints for Terraform execution (INTERNAL ONLY).
API ONLY enqueues jobs - NEVER executes Terraform directly.
"""
import json
import redis
from fastapi import APIRouter, HTTPException, status
from app.models.request import ExecutionRequest
from app.models.response import ExecutionResponse
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/internal", tags=["internal"])

# Redis client for job queue
redis_client = None


def get_redis():
    """Get Redis client (lazy initialization)."""
    global redis_client
    if redis_client is None:
        import os
        redis_client = redis.from_url(
            os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
            decode_responses=True
        )
    return redis_client


@router.post("/execute", response_model=ExecutionResponse, status_code=status.HTTP_202_ACCEPTED)
async def execute(request: ExecutionRequest):
    """
    Enqueue Terraform execution job.
    
    API ONLY enqueues - worker process executes.
    Returns immediately (202 Accepted).
    """
    logger.info(f"Enqueuing execution request for job {request.job_id}")
    
    # Validate request
    if not request.workspace_reference:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="workspace_reference is required"
        )
    
    # Enqueue job
    try:
        job_data = {
            "job_id": request.job_id,
            "workspace_reference": request.workspace_reference,
            "credential_reference": request.credential_reference
        }
        
        queue_name = "terraform:jobs"
        r = get_redis()
        r.lpush(queue_name, json.dumps(job_data))
        
        logger.info(f"Job {request.job_id} enqueued successfully")
        
        return ExecutionResponse(
            success=True,
            job_id=request.job_id,
            plan_reference=None,  # Will be available after worker execution
            metadata=None
        )
    
    except Exception as e:
        logger.error(f"Failed to enqueue job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enqueue job: {str(e)}"
        )


@router.get("/status/{job_id}")
async def get_status(job_id: str):
    """
    Get job execution status.
    
    Checks result from worker in Redis.
    """
    try:
        r = get_redis()
        result_key = f"terraform:result:{job_id}"
        result_json = r.get(result_key)
        
        if result_json is None:
            return {
                "job_id": job_id,
                "status": "pending",
                "message": "Job is queued or in progress"
            }
        
        result = json.loads(result_json)
        return result
    
    except Exception as e:
        logger.error(f"Failed to get status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}"
        )

