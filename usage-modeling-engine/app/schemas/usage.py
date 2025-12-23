"""
Usage schemas and models.
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum


class UsageConfidence(str, Enum):
    """Confidence level for usage assumptions."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class UsageScenario(BaseModel):
    """Usage scenario with min/expected/max values."""
    
    min: float = Field(..., description="Minimum usage (conservative lower bound)")
    expected: float = Field(..., description="Expected usage (most likely)")
    max: float = Field(..., description="Maximum usage (peak/worst-case)")
    unit: str = Field(..., description="Usage unit (hours, GB, requests, etc.)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "min": 160.0,
                "expected": 730.0,
                "max": 730.0,
                "unit": "hours"
            }
        }


class UsageAnnotation(BaseModel):
    """Usage annotation for a resource."""
    
    usage_scenarios: Dict[str, UsageScenario] = Field(
        default_factory=dict,
        description="Usage scenarios by dimension (e.g., 'instance_hours', 'storage_gb')"
    )
    usage_profile: str = Field(..., description="Profile applied (dev/stage/prod/custom)")
    usage_confidence: UsageConfidence = Field(..., description="Confidence in usage assumptions")
    usage_assumptions: List[str] = Field(
        default_factory=list,
        description="Human-readable usage assumptions"
    )
    overrides_applied: List[str] = Field(
        default_factory=list,
        description="List of overrides applied"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "usage_scenarios": {
                    "instance_hours": {
                        "min": 160.0,
                        "expected": 730.0,
                        "max": 730.0,
                        "unit": "hours"
                    }
                },
                "usage_profile": "prod",
                "usage_confidence": "MEDIUM",
                "usage_assumptions": [
                    "24x7 uptime assumed for production",
                    "No autoscaling configured"
                ],
                "overrides_applied": []
            }
        }


class UsageOverride(BaseModel):
    """Override for usage assumptions."""
    
    resource_id: Optional[str] = Field(None, description="Specific resource ID (if resource-level)")
    service: Optional[str] = Field(None, description="Service type (if service-level)")
    dimension: str = Field(..., description="Usage dimension to override")
    value: float = Field(..., description="Override value")
    scenario: Optional[str] = Field(None, description="Scenario to override (min/expected/max)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "resource_id": "aws_instance.web",
                "service": None,
                "dimension": "instance_hours",
                "value": 730.0,
                "scenario": "expected"
            }
        }


class UsageAnnotatedResource(BaseModel):
    """Resource with usage annotations."""
    
    resource_id: str
    resource_type: str
    service: str
    region: str
    attributes: Dict[str, Any] = Field(default_factory=dict)
    usage_annotation: UsageAnnotation
    
    class Config:
        json_schema_extra = {
            "example": {
                "resource_id": "aws_instance.web",
                "resource_type": "instance",
                "service": "ec2",
                "region": "us-east-1",
                "attributes": {
                    "instanceType": "t3.micro"
                },
                "usage_annotation": {}
            }
        }


class UARG(BaseModel):
    """Usage-Annotated Resource Graph."""
    
    resources: List[UsageAnnotatedResource] = Field(
        default_factory=list,
        description="List of usage-annotated resources"
    )
    profile_applied: str = Field(..., description="Usage profile applied")
    profile_version: str = Field(..., description="Profile version")
    overrides_count: int = Field(default=0, description="Number of overrides applied")
    
    class Config:
        json_schema_extra = {
            "example": {
                "resources": [],
                "profile_applied": "prod",
                "profile_version": "v1",
                "overrides_count": 0
            }
        }


class ApplyUsageRequest(BaseModel):
    """Request to apply usage to resources."""
    
    resources: List[Dict[str, Any]] = Field(..., description="Resources from ERG")
    profile: Optional[str] = Field(None, description="Usage profile to apply")
    overrides: List[UsageOverride] = Field(default_factory=list, description="Usage overrides")
    
    class Config:
        json_schema_extra = {
            "example": {
                "resources": [],
                "profile": "prod",
                "overrides": []
            }
        }


class ApplyUsageResponse(BaseModel):
    """Response from usage application."""
    
    uarg: UARG = Field(..., description="Usage-annotated resource graph")
    
    class Config:
        json_schema_extra = {
            "example": {
                "uarg": {
                    "resources": [],
                    "profile_applied": "prod",
                    "profile_version": "v1",
                    "overrides_count": 0
                }
            }
        }
