"""
API request/response models.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any


class NRGNode(BaseModel):
    """Normalized Resource Graph Node (input from Plan Interpreter)."""
    
    resource_id: str
    terraform_address: str
    resource_type: str
    provider: str
    region: str | None
    attributes: Dict[str, Any]
    unknown_attributes: List[str]
    quantity: int
    module_path: List[str]
    dependencies: List[str]
    confidence_level: str


class EnrichRequest(BaseModel):
    """Request to enrich NRG."""
    
    normalized_resource_graph: List[NRGNode] = Field(..., description="NRG from Plan Interpreter")
    aws_account_id: str | None = Field(None, description="AWS account ID (optional)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "normalized_resource_graph": [],
                "aws_account_id": "123456789012"
            }
        }


class EnrichResponse(BaseModel):
    """Response from enrichment."""
    
    enriched_resource_graph: List[Dict[str, Any]] = Field(..., description="ERG nodes")
    enrichment_metadata: Dict[str, Any] = Field(..., description="Enrichment metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "enriched_resource_graph": [],
                "enrichment_metadata": {
                    "total_resources": 0,
                    "terraform_resources": 0,
                    "implicit_resources": 0
                }
            }
        }
