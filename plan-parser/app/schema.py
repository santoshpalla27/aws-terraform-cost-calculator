"""Normalized Resource Graph (NRG) schema."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class NRGResource(BaseModel):
    """Normalized resource in the graph."""
    
    resource_id: str = Field(..., description="Unique resource identifier (e.g., aws_instance.web[0])")
    resource_type: str = Field(..., description="Resource type (e.g., aws_instance)")
    provider: str = Field(..., description="Cloud provider (e.g., aws, azurerm, google)")
    region: Optional[str] = Field(default=None, description="Cloud region")
    quantity: int = Field(default=1, description="Number of instances (resolved from count/for_each)")
    module_path: List[str] = Field(default_factory=lambda: ["root"], description="Module hierarchy")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Resource attributes")
    computed_attributes: List[str] = Field(default_factory=list, description="Attributes with unknown values")
    confidence: float = Field(default=1.0, description="Confidence score (0.0-1.0)", ge=0.0, le=1.0)
    parent_id: Optional[str] = Field(default=None, description="Parent resource ID")
    children: List[str] = Field(default_factory=list, description="Child resource IDs")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "resource_id": "aws_instance.web[0]",
                "resource_type": "aws_instance",
                "provider": "aws",
                "region": "us-east-1",
                "quantity": 1,
                "module_path": ["root"],
                "attributes": {
                    "ami": "ami-0c55b159cbfafe1f0",
                    "instance_type": "t3.medium"
                },
                "computed_attributes": ["id", "public_ip"],
                "confidence": 0.85,
                "parent_id": None,
                "children": [],
                "metadata": {"action": "create"}
            }
        }


class NRGMetadata(BaseModel):
    """Metadata about the resource graph."""
    
    total_resources: int = Field(..., description="Total number of resources")
    providers: List[str] = Field(default_factory=list, description="List of providers used")
    regions: List[str] = Field(default_factory=list, description="List of regions used")
    modules: List[str] = Field(default_factory=list, description="List of modules")
    resource_types: Dict[str, int] = Field(default_factory=dict, description="Count by resource type")


class NRG(BaseModel):
    """Normalized Resource Graph."""
    
    resources: List[NRGResource] = Field(default_factory=list, description="List of resources")
    metadata: NRGMetadata = Field(..., description="Graph metadata")
    terraform_version: str = Field(..., description="Terraform version")
    format_version: str = Field(..., description="Plan format version")
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "resources": [],
                "metadata": {
                    "total_resources": 5,
                    "providers": ["aws"],
                    "regions": ["us-east-1"],
                    "modules": ["root"],
                    "resource_types": {"aws_instance": 3, "aws_s3_bucket": 2}
                },
                "terraform_version": "1.6.6",
                "format_version": "1.2"
            }
        }
