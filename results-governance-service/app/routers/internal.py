"""
Internal results API router.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from app.schemas.result import (
    StoreResultRequest,
    StoreResultResponse,
    ResultDetail,
    HistoryQuery,
    HistoryResponse
)
from app.models.cost_result import CostResult
from app.persistence.database import get_db
from app.persistence.result_repository import ResultRepository
from app.persistence.audit_repository import AuditRepository
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/internal/results", tags=["results"])


@router.post("/store", response_model=StoreResultResponse)
async def store_result(
    request: StoreResultRequest,
    db: Session = Depends(get_db)
):
    """
    Store cost result (append-only).
    
    Args:
        request: Store result request
        db: Database session
        
    Returns:
        Store result response
    """
    logger.info(f"Storing result: project={request.project_id}, env={request.environment}")
    
    try:
        # Extract FCM data
        fcm_data = request.fcm
        determinism_hash = fcm_data.get('determinism_hash', 'unknown')
        overall_confidence = fcm_data.get('overall_confidence', 'LOW')
        
        # Create cost result
        cost_result = CostResult(
            project_id=request.project_id,
            environment=request.environment,
            fcm=fcm_data,
            determinism_hash=determinism_hash,
            overall_confidence=overall_confidence,
            git_commit=request.git_commit,
            build_id=request.build_id,
            trigger=request.trigger
        )
        
        # Store result
        repo = ResultRepository(db)
        stored_result = repo.store_result(cost_result)
        
        # Audit log
        audit_repo = AuditRepository(db)
        audit_repo.log_action(
            action="persist",
            actor="system",
            input_data={"project_id": request.project_id, "environment": request.environment},
            outcome={"result_id": str(stored_result.result_id)}
        )
        
        logger.info(f"Stored result: {stored_result.result_id}")
        
        return StoreResultResponse(
            result_id=stored_result.result_id,
            determinism_hash=stored_result.determinism_hash,
            timestamp=stored_result.timestamp
        )
        
    except Exception as e:
        logger.error(f"Failed to store result: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to store result")


@router.get("/{result_id}", response_model=ResultDetail)
async def get_result(
    result_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get cost result by ID.
    
    Args:
        result_id: Result ID
        db: Database session
        
    Returns:
        Result detail
    """
    logger.info(f"Retrieving result: {result_id}")
    
    repo = ResultRepository(db)
    result = repo.get_result(result_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    
    return ResultDetail.from_orm(result)


@router.post("/history", response_model=HistoryResponse)
async def query_history(
    query: HistoryQuery,
    db: Session = Depends(get_db)
):
    """
    Query historical cost results.
    
    Args:
        query: History query
        db: Database session
        
    Returns:
        History response
    """
    logger.info(f"Querying history: project={query.project_id}, env={query.environment}")
    
    repo = ResultRepository(db)
    results = repo.query_history(
        project_id=query.project_id,
        environment=query.environment,
        start_date=query.start_date,
        end_date=query.end_date,
        limit=query.limit
    )
    
    return HistoryResponse(
        results=[ResultDetail.from_orm(r) for r in results],
        count=len(results)
    )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "results-governance-service"
    }
