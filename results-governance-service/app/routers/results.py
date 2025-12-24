"""
API router for cost results with immutability enforcement.

CRITICAL: Only POST (create) and GET (read) are allowed.
PUT, PATCH, DELETE return 405 Method Not Allowed.
"""
from fastapi import APIRouter, HTTPException, status
from typing import List
from app.models.cost_result import CostResult, ResultSummary
from app.models.exceptions import (
    ImmutableResultError,
    ResultAlreadyExistsError,
    ResultNotFoundError
)
from app.persistence.result_repository import result_repository
from app.utils.logger import get_logger
import uuid

logger = get_logger(__name__)
router = APIRouter(prefix="/api/results", tags=["results"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_result(result: CostResult):
    """
    Create a new cost result (WRITE-ONCE).
    
    CRITICAL: Results can only be created once per job.
    Attempting to create a duplicate will return 409 Conflict.
    """
    correlation_id = str(uuid.uuid4())
    
    try:
        created_result = await result_repository.create(result)
        
        logger.info(
            f"Result created successfully for job {result.job_id}",
            extra={
                "job_id": result.job_id,
                "result_id": created_result.result_id,
                "correlation_id": correlation_id
            }
        )
        
        return {
            "success": True,
            "data": created_result,
            "error": None,
            "correlation_id": correlation_id
        }
        
    except ResultAlreadyExistsError as e:
        logger.warning(
            f"Duplicate result creation attempt: {str(e)}",
            extra={
                "job_id": result.job_id,
                "correlation_id": correlation_id
            }
        )
        
        return {
            "success": False,
            "data": None,
            "error": {
                "code": "RESULT_ALREADY_EXISTS",
                "message": str(e)
            },
            "correlation_id": correlation_id
        }


@router.get("/{job_id}")
async def get_result(job_id: str):
    """
    Get cost result by job ID (read-only).
    """
    correlation_id = str(uuid.uuid4())
    
    result = await result_repository.get_by_job_id(job_id)
    
    if not result:
        return {
            "success": False,
            "data": None,
            "error": {
                "code": "RESULT_NOT_FOUND",
                "message": f"Result for job {job_id} not found"
            },
            "correlation_id": correlation_id
        }
    
    return {
        "success": True,
        "data": result,
        "error": None,
        "correlation_id": correlation_id
    }


@router.get("")
async def list_results(project_id: str, limit: int = 10, offset: int = 0):
    """
    List results for historical comparison (read-only).
    
    Query params:
    - project_id: Project identifier
    - limit: Max results (default 10)
    - offset: Pagination offset (default 0)
    
    Returns results ordered by created_at DESC.
    """
    correlation_id = str(uuid.uuid4())
    
    results = await result_repository.list_by_project(
        project_id=project_id,
        limit=limit,
        offset=offset
    )
    
    return {
        "success": True,
        "data": results,
        "error": None,
        "correlation_id": correlation_id
    }


# FORBIDDEN OPERATIONS
# These endpoints return 405 Method Not Allowed

@router.put("/{result_id}")
async def update_result(result_id: str):
    """
    Update result (FORBIDDEN).
    
    Results are immutable and cannot be updated.
    """
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail="Cost results are immutable and cannot be updated. Create a new job to generate new results."
    )


@router.patch("/{result_id}")
async def patch_result(result_id: str):
    """
    Patch result (FORBIDDEN).
    
    Results are immutable and cannot be modified.
    """
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail="Cost results are immutable and cannot be modified. Create a new job to generate new results."
    )


@router.delete("/{result_id}")
async def delete_result(result_id: str):
    """
    Delete result (FORBIDDEN).
    
    Results are permanent for audit and compliance.
    """
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail="Cost results are immutable and cannot be deleted. Results are permanent for audit and compliance."
    )
