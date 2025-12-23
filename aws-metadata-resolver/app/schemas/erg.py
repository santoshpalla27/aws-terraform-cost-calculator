"""
Enriched Resource Graph (ERG) schema.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class ResourceProvenance(str, Enum):
    """Source of resource in ERG."""
    TERRAFORM = "terraform"  # Explicitly declared in Terraform
    IMPLICIT = "implicit"    # Implicitly created by AWS
    DERIVED = "derived"      # Derived from AWS API calls


class ConfidenceLevel(str, Enum):
    """Confidence in enriched metadata."""
    HIGH = "HIGH"      # All metadata resolved
    MEDIUM = "MEDIUM"  # Some metadata missing
    LOW = "LOW"        # Significant metadata gaps


class ERGNode(BaseModel):
    """Enriched Resource Graph Node."""
    
    # From NRG (preserved)
    resource_id: str = Field(..., description="Deterministic resource ID")
    terraform_address: Optional[str] = Field(None, description="Terraform address (null for implicit)")
    resource_type: str = Field(..., description="AWS resource type")
    provider: str = Field(..., description="Cloud provider (aws)")
    region: Optional[str] = Field(None, description="AWS region")
    quantity: int = Field(1, description="Resource quantity")
    module_path: List[str] = Field(default_factory=list, description="Terraform module path")
    dependencies: List[str] = Field(default_factory=list, description="Dependency resource IDs")
    
    # Enriched attributes
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Known attributes")
    unknown_attributes: List[str] = Field(default_factory=list, description="Unknown attributes")
    enriched_attributes: Dict[str, Any] = Field(default_factory=dict, description="AWS-enriched attributes")
    
    # Metadata
    provenance: ResourceProvenance = Field(ResourceProvenance.TERRAFORM, description="Resource source")
    parent_resource_id: Optional[str] = Field(None, description="Parent resource (for implicit)")
    confidence_level: ConfidenceLevel = Field(ConfidenceLevel.HIGH, description="Enrichment confidence")
    
    # AWS-specific
    aws_account_id: Optional[str] = Field(None, description="AWS account ID")
    availability_zone: Optional[str] = Field(None, description="Availability zone")
    
    class Config:
        json_schema_extra = {
            "example": {
                "resource_id": "a1b2c3d4e5f6g7h8",
                "terraform_address": "aws_instance.web",
                "resource_type": "aws_instance",
                "provider": "aws",
                "region": "us-east-1",
                "quantity": 1,
                "attributes": {"instance_type": "t3.micro"},
                "enriched_attributes": {"tenancy": "default", "ebs_optimized": False},
                "provenance": "terraform",
                "confidence_level": "HIGH"
            }
        }


class EnrichmentMetadata(BaseModel):
    """Metadata about enrichment process."""
    
    total_resources: int = Field(..., description="Total resources in ERG")
    terraform_resources: int = Field(..., description="Resources from Terraform")
    implicit_resources: int = Field(..., description="Implicitly created resources")
    enriched_count: int = Field(..., description="Resources successfully enriched")
    failed_count: int = Field(..., description="Resources that failed enrichment")
    cache_hit_rate: float = Field(..., description="Cache hit rate (0-1)")
    aws_api_calls: int = Field(..., description="Total AWS API calls made")
    enrichment_duration_ms: int = Field(..., description="Enrichment duration in ms")
    enrichment_timestamp: datetime = Field(..., description="When enrichment occurred")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_resources": 15,
                "terraform_resources": 10,
                "implicit_resources": 5,
                "enriched_count": 14,
                "failed_count": 1,
                "cache_hit_rate": 0.75,
                "aws_api_calls": 8,
                "enrichment_duration_ms": 1250,
                "enrichment_timestamp": "2024-01-15T10:30:00Z"
            }
        }


class EnrichedResourceGraph(BaseModel):
    """Complete Enriched Resource Graph."""
    
    nodes: List[ERGNode] = Field(..., description="ERG nodes")
    metadata: EnrichmentMetadata = Field(..., description="Enrichment metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "nodes": [],
                "metadata": {
                    "total_resources": 0,
                    "terraform_resources": 0,
                    "implicit_resources": 0
                }
            }
        }
