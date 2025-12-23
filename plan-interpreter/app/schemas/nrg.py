"""
Normalized Resource Graph (NRG) schema.
Cloud-agnostic, Terraform-free representation.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class ConfidenceLevel(str, Enum):
    """Confidence level for resource interpretation."""
    HIGH = "HIGH"       # All attributes known
    MEDIUM = "MEDIUM"   # Some unknowns, but key attrs known
    LOW = "LOW"         # Many unknowns


class NRGNode(BaseModel):
    """Single node in the Normalized Resource Graph."""
    
    # Identity
    resource_id: str = Field(..., description="Unique, deterministic ID")
    terraform_address: str = Field(..., description="Full Terraform address")
    
    # Classification
    resource_type: str = Field(..., description="Resource type (e.g., aws_instance)")
    provider: str = Field(..., description="Provider (e.g., aws)")
    region: Optional[str] = Field(None, description="Region if known")
    
    # Attributes
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Resolved attributes")
    unknown_attributes: List[str] = Field(default_factory=list, description="Attributes marked UNKNOWN")
    
    # Metadata
    quantity: int = Field(1, description="Always 1 per node")
    module_path: List[str] = Field(default_factory=list, description="Module hierarchy")
    
    # Dependencies
    dependencies: List[str] = Field(default_factory=list, description="Resource IDs of dependencies")
    
    # Confidence
    confidence_level: ConfidenceLevel = Field(default=ConfidenceLevel.HIGH)
    
    class Config:
        json_schema_extra = {
            "example": {
                "resource_id": "a1b2c3d4e5f6g7h8",
                "terraform_address": "module.vpc.aws_subnet.private[0]",
                "resource_type": "aws_subnet",
                "provider": "aws",
                "region": "us-east-1",
                "attributes": {
                    "cidr_block": "10.0.1.0/24",
                    "availability_zone": "us-east-1a"
                },
                "unknown_attributes": ["id"],
                "quantity": 1,
                "module_path": ["module.vpc"],
                "dependencies": ["aws_vpc.main"],
                "confidence_level": "MEDIUM"
            }
        }


class InterpretationMetadata(BaseModel):
    """Metadata about the interpretation process."""
    
    plan_hash: str = Field(..., description="Deterministic hash of input plan")
    total_resources: int = Field(..., description="Total number of resources")
    resources_by_type: Dict[str, int] = Field(default_factory=dict, description="Count by resource type")
    unknown_value_count: int = Field(0, description="Total unknown attributes")
    module_depth: int = Field(0, description="Maximum module nesting depth")
    interpretation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "plan_hash": "abc123def456",
                "total_resources": 42,
                "resources_by_type": {
                    "aws_instance": 5,
                    "aws_s3_bucket": 2
                },
                "unknown_value_count": 3,
                "module_depth": 2,
                "interpretation_timestamp": "2024-01-01T12:00:00Z"
            }
        }


class NormalizedResourceGraph(BaseModel):
    """Complete Normalized Resource Graph."""
    
    nodes: List[NRGNode] = Field(..., description="Resource nodes")
    metadata: InterpretationMetadata = Field(..., description="Interpretation metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "nodes": [],
                "metadata": {
                    "plan_hash": "abc123",
                    "total_resources": 0,
                    "resources_by_type": {},
                    "unknown_value_count": 0,
                    "module_depth": 0
                }
            }
        }
