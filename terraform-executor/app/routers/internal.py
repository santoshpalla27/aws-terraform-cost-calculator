"""
Internal API endpoints for Terraform execution (INTERNAL ONLY).
Implements async execution contract with execution_id tracking.
"""
import os
from fastapi import APIRouter, HTTPException, status
from app.models.execution import (
    TerraformExecutionRequest,
    TerraformExecutionResponse,
    ExecutionStatusResponse,
    ExecutionResultResponse,
    ExecutionStatus
)
from app.services.execution_manager import ExecutionManager
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/internal/terraform", tags=["terraform-execution"])

# Execution manager (lazy initialization)
_execution_manager = None


def get_execution_manager() -> ExecutionManager:
    """Get execution manager instance."""
    global _execution_manager
    if _execution_manager is None:
        redis_url = os.environ.get("REDIS_URL", "redis://redis:6379/0")
        _execution_manager = ExecutionManager(redis_url)
    return _execution_manager


@router.post("/execute", response_model=TerraformExecutionResponse, status_code=status.HTTP_202_ACCEPTED)
async def execute_terraform(request: TerraformExecutionRequest):
    """
    Submit Terraform execution request.
    
    Returns execution_id immediately. Execution happens asynchronously.
    Poll /status/{execution_id} to check progress.
    """
    logger.info(f"Received execution request for job {request.job_id}")
    
    try:
        manager = get_execution_manager()
        execution_id = manager.create_execution(
            job_id=request.job_id,
            terraform_source=request.terraform_source,
            variables=request.variables
        )
        
        logger.info(f"Created execution {execution_id} for job {request.job_id}")
        
        return TerraformExecutionResponse(
            execution_id=execution_id,
            job_id=request.job_id,
            status=ExecutionStatus.PENDING
        )
    
    except Exception as e:
        logger.error(f"Failed to create execution: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create execution: {str(e)}"
        )


@router.get("/status/{execution_id}", response_model=ExecutionStatusResponse)
async def get_execution_status(execution_id: str):
    """
    Get execution status.
    
    Returns: PENDING | RUNNING | COMPLETED | FAILED | TIMEOUT | KILLED
    """
    try:
        manager = get_execution_manager()
        status_response = manager.get_status(execution_id)
        
        if not status_response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Execution {execution_id} not found"
            )
        
        return status_response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}"
        )


@router.get("/result/{execution_id}", response_model=ExecutionResultResponse)
async def get_execution_result(execution_id: str):
    """
    Get execution result (plan.json).
    
    Only available after execution completes.
    Returns 404 if execution not found.
    Returns 409 if execution not yet completed.
    """
    try:
        manager = get_execution_manager()
        result = manager.get_result(execution_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Execution {execution_id} not found"
            )
        
        if result.status not in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Execution {execution_id} is {result.status.value}, not yet completed"
            )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get result: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get result: {str(e)}"
        )


@router.delete("/execution/{execution_id}", status_code=status.HTTP_204_NO_CONTENT)
async def kill_execution(execution_id: str):
    """
    Kill a running execution.
    
    Marks execution as KILLED. Worker should check status and terminate.
    """
    try:
        manager = get_execution_manager()
        manager.kill_execution(execution_id)
        logger.info(f"Killed execution {execution_id}")
    
    except Exception as e:
        logger.error(f"Failed to kill execution: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to kill execution: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "terraform-executor"}
