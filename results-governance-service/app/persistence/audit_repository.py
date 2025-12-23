"""
Audit repository for immutable audit logging.
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AuditRepository:
    """Repository for immutable audit logging."""
    
    def __init__(self, db: Session):
        """
        Initialize repository.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def log_action(
        self,
        action: str,
        actor: Optional[str] = None,
        correlation_id: Optional[str] = None,
        input_data: Optional[dict] = None,
        outcome: Optional[dict] = None
    ) -> AuditLog:
        """
        Log an action (immutable).
        
        Args:
            action: Action type (persist, compare, policy_eval, gate)
            actor: Actor (user or service)
            correlation_id: Correlation ID for tracing
            input_data: Input data
            outcome: Outcome data
            
        Returns:
            Audit log entry
        """
        audit_log = AuditLog(
            action=action,
            actor=actor,
            correlation_id=correlation_id,
            input_data=input_data,
            outcome=outcome
        )
        
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        
        logger.info(f"Logged action: {action} (audit_id={audit_log.audit_id})")
        
        return audit_log
    
    def query_audit(
        self,
        action: Optional[str] = None,
        correlation_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Query audit logs.
        
        Args:
            action: Action filter (optional)
            correlation_id: Correlation ID filter (optional)
            start_date: Start date filter (optional)
            end_date: End date filter (optional)
            limit: Result limit
            
        Returns:
            List of audit logs
        """
        query = self.db.query(AuditLog)
        
        if action:
            query = query.filter(AuditLog.action == action)
        
        if correlation_id:
            query = query.filter(AuditLog.correlation_id == correlation_id)
        
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        
        results = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
        
        logger.info(f"Queried audit logs: {len(results)} results")
        
        return results
