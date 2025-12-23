"""
Result repository for cost result persistence.
"""
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.cost_result import CostResult
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ResultRepository:
    """Repository for cost result persistence (append-only)."""
    
    def __init__(self, db: Session):
        """
        Initialize repository.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def store_result(self, cost_result: CostResult) -> CostResult:
        """
        Store cost result (append-only, no updates).
        
        Args:
            cost_result: Cost result to store
            
        Returns:
            Stored cost result
        """
        self.db.add(cost_result)
        self.db.commit()
        self.db.refresh(cost_result)
        
        logger.info(f"Stored cost result: {cost_result.result_id}")
        
        return cost_result
    
    def get_result(self, result_id: UUID) -> Optional[CostResult]:
        """
        Get cost result by ID.
        
        Args:
            result_id: Result ID
            
        Returns:
            Cost result or None
        """
        return self.db.query(CostResult).filter(
            CostResult.result_id == result_id
        ).first()
    
    def query_history(
        self,
        project_id: str,
        environment: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[CostResult]:
        """
        Query historical cost results.
        
        Args:
            project_id: Project ID
            environment: Environment filter (optional)
            start_date: Start date filter (optional)
            end_date: End date filter (optional)
            limit: Result limit
            
        Returns:
            List of cost results
        """
        query = self.db.query(CostResult).filter(
            CostResult.project_id == project_id
        )
        
        if environment:
            query = query.filter(CostResult.environment == environment)
        
        if start_date:
            query = query.filter(CostResult.timestamp >= start_date)
        
        if end_date:
            query = query.filter(CostResult.timestamp <= end_date)
        
        results = query.order_by(CostResult.timestamp.desc()).limit(limit).all()
        
        logger.info(f"Queried history: {len(results)} results for project {project_id}")
        
        return results
    
    def get_latest_result(
        self,
        project_id: str,
        environment: str
    ) -> Optional[CostResult]:
        """
        Get latest cost result for project/environment.
        
        Args:
            project_id: Project ID
            environment: Environment
            
        Returns:
            Latest cost result or None
        """
        return self.db.query(CostResult).filter(
            and_(
                CostResult.project_id == project_id,
                CostResult.environment == environment
            )
        ).order_by(CostResult.timestamp.desc()).first()
