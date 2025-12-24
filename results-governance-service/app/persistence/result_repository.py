"""
Result repository with WRITE-ONCE semantics.

CRITICAL: Results can only be created, never updated or deleted.
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError
from app.models.cost_result import CostResult, ResultSummary
from app.models.exceptions import (
    ImmutableResultError,
    ResultAlreadyExistsError,
    ResultNotFoundError
)
from app.persistence.database import get_db_session
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ResultRepository:
    """
    Repository for cost results with immutability enforcement.
    
    CRITICAL RULES:
    - create(): Write-once, throws if duplicate
    - update(): FORBIDDEN, always throws
    - delete(): FORBIDDEN, always throws
    - get/list(): Read-only operations
    """
    
    def __init__(self):
        self.session = get_db_session()
    
    async def create(self, result: CostResult) -> CostResult:
        """
        Create a new cost result (WRITE-ONCE).
        
        Args:
            result: Cost result to create
            
        Returns:
            Created result
            
        Raises:
            ResultAlreadyExistsError: If result for job_id already exists
        """
        # Check if result already exists for this job
        existing = await self.get_by_job_id(result.job_id)
        if existing:
            logger.error(
                f"Attempt to create duplicate result for job {result.job_id}",
                extra={
                    "job_id": result.job_id,
                    "existing_result_id": existing.result_id,
                    "correlation_id": result.correlation_id
                }
            )
            raise ResultAlreadyExistsError(
                f"Result for job {result.job_id} already exists. "
                f"Results are immutable and cannot be recreated."
            )
        
        try:
            # Insert result (write-once)
            logger.info(
                f"Creating immutable result for job {result.job_id}",
                extra={
                    "job_id": result.job_id,
                    "result_id": result.result_id,
                    "total_cost": float(result.total_monthly_cost),
                    "correlation_id": result.correlation_id
                }
            )
            
            # Database insert logic here
            # await self.session.execute(insert_statement)
            # await self.session.commit()
            
            return result
            
        except IntegrityError as e:
            logger.error(
                f"Database integrity error creating result: {e}",
                extra={
                    "job_id": result.job_id,
                    "correlation_id": result.correlation_id
                }
            )
            raise ResultAlreadyExistsError(
                f"Result for job {result.job_id} already exists"
            )
    
    async def update(self, result: CostResult) -> None:
        """
        Update a result (FORBIDDEN).
        
        Raises:
            ImmutableResultError: Always
        """
        logger.error(
            f"Attempt to update immutable result {result.result_id}",
            extra={
                "result_id": result.result_id,
                "job_id": result.job_id
            }
        )
        raise ImmutableResultError(
            "Cost results are immutable and cannot be updated. "
            "Create a new job to generate new results."
        )
    
    async def delete(self, result_id: str) -> None:
        """
        Delete a result (FORBIDDEN).
        
        Raises:
            ImmutableResultError: Always
        """
        logger.error(
            f"Attempt to delete immutable result {result_id}",
            extra={"result_id": result_id}
        )
        raise ImmutableResultError(
            "Cost results are immutable and cannot be deleted. "
            "Results are permanent for audit and compliance."
        )
    
    async def get_by_id(self, result_id: str) -> Optional[CostResult]:
        """
        Get result by ID (read-only).
        
        Args:
            result_id: Result ID
            
        Returns:
            Cost result or None
        """
        logger.debug(
            f"Fetching result {result_id}",
            extra={"result_id": result_id}
        )
        
        # Database query logic here
        # result = await self.session.execute(select_statement)
        # return result.scalar_one_or_none()
        
        return None  # Placeholder
    
    async def get_by_job_id(self, job_id: str) -> Optional[CostResult]:
        """
        Get result by job ID (read-only).
        
        Args:
            job_id: Job ID
            
        Returns:
            Cost result or None
        """
        logger.debug(
            f"Fetching result for job {job_id}",
            extra={"job_id": job_id}
        )
        
        # Database query logic here
        # result = await self.session.execute(
        #     select(CostResult).where(CostResult.job_id == job_id)
        # )
        # return result.scalar_one_or_none()
        
        return None  # Placeholder
    
    async def list_by_project(
        self,
        project_id: str,
        limit: int = 10,
        offset: int = 0
    ) -> List[ResultSummary]:
        """
        List results for a project (read-only, for historical comparison).
        
        Args:
            project_id: Project ID
            limit: Max results to return
            offset: Offset for pagination
            
        Returns:
            List of result summaries, ordered by created_at DESC
        """
        logger.debug(
            f"Listing results for project {project_id}",
            extra={
                "project_id": project_id,
                "limit": limit,
                "offset": offset
            }
        )
        
        # Database query logic here
        # results = await self.session.execute(
        #     select(CostResult)
        #     .where(CostResult.project_id == project_id)
        #     .order_by(CostResult.created_at.desc())
        #     .limit(limit)
        #     .offset(offset)
        # )
        # return [ResultSummary.from_orm(r) for r in results.scalars()]
        
        return []  # Placeholder


# Singleton instance
result_repository = ResultRepository()
