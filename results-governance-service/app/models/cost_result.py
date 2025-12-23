"""
Cost Result database model.
"""
from sqlalchemy import Column, String, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
from app.persistence.database import Base


class CostResult(Base):
    """Cost result - immutable record of FCM."""
    
    __tablename__ = "cost_results"
    
    # Primary key
    result_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Metadata
    project_id = Column(String(255), nullable=False, index=True)
    environment = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # FCM data (JSONB for flexibility and queryability)
    fcm = Column(JSONB, nullable=False)
    
    # Verification
    determinism_hash = Column(String(64), nullable=False, index=True)
    overall_confidence = Column(String(20), nullable=False)
    
    # Build metadata
    git_commit = Column(String(255), nullable=True)
    build_id = Column(String(255), nullable=True)
    trigger = Column(String(50), nullable=True)  # manual, ci, scheduled
    
    # Audit
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_project_env_time', 'project_id', 'environment', 'timestamp'),
        Index('idx_determinism_hash', 'determinism_hash'),
    )
    
    def __repr__(self):
        return f"<CostResult(result_id={self.result_id}, project={self.project_id}, env={self.environment})>"
