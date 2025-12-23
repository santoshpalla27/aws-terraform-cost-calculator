"""
Audit Log database model.
"""
from sqlalchemy import Column, String, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
from app.persistence.database import Base


class AuditLog(Base):
    """Audit log - immutable record of all actions."""
    
    __tablename__ = "audit_logs"
    
    # Primary key
    audit_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Timestamp
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Action details
    action = Column(String(50), nullable=False, index=True)  # persist, compare, policy_eval, gate
    actor = Column(String(255), nullable=True)  # user or service
    correlation_id = Column(String(255), nullable=True, index=True)
    
    # Input/Output
    input_data = Column(JSONB, nullable=True)
    outcome = Column(JSONB, nullable=True)
    
    # Indexes for queries
    __table_args__ = (
        Index('idx_action_time', 'action', 'timestamp'),
        Index('idx_correlation', 'correlation_id'),
    )
    
    def __repr__(self):
        return f"<AuditLog(audit_id={self.audit_id}, action={self.action}, timestamp={self.timestamp})>"
