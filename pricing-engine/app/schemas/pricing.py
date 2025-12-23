"""
Pricing schemas and models.
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class PricingUnit(str, Enum):
    """Pricing unit types."""
    HOUR = "Hour"
    GB_MONTH = "GB-Month"
    GB = "GB"
    REQUEST = "Request"
    LCU_HOUR = "LCU-Hour"
    CONNECTION_HOUR = "Connection-Hour"


class ConfidenceLevel(str, Enum):
    """Confidence level for pricing data."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class PricingDimension(BaseModel):
    """Billable dimension metadata."""
    
    dimension_key: str
    description: str
    unit: PricingUnit
    price_per_unit: float
    begin_range: Optional[str] = None
    end_range: Optional[str] = None


class NormalizedPrice(BaseModel):
    """Canonical price record."""
    
    service: str = Field(..., description="AWS service (ec2, ebs, elb, etc.)")
    resource_type: str = Field(..., description="Resource type (instance, volume, load_balancer)")
    usage_type: str = Field(..., description="Usage type from AWS")
    region: str = Field(..., description="AWS region code")
    unit: PricingUnit = Field(..., description="Pricing unit")
    price_per_unit: float = Field(..., description="Price per unit in USD")
    currency: str = Field(default="USD", description="Currency code")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Resource attributes")
    effective_date: datetime = Field(..., description="When this price became effective")
    sku: str = Field(..., description="AWS SKU")
    
    class Config:
        json_schema_extra = {
            "example": {
                "service": "ec2",
                "resource_type": "instance",
                "usage_type": "BoxUsage:t3.micro",
                "region": "us-east-1",
                "unit": "Hour",
                "price_per_unit": 0.0104,
                "currency": "USD",
                "attributes": {
                    "instanceType": "t3.micro",
                    "tenancy": "Shared",
                    "operatingSystem": "Linux"
                },
                "effective_date": "2024-01-01T00:00:00Z",
                "sku": "ABC123DEF456"
            }
        }


class PricingMetadata(BaseModel):
    """Pricing version and metadata."""
    
    service: str
    version: str
    publication_date: datetime
    last_updated: datetime
    source: str = "AWS Price List API"
    total_skus: int = 0


class PriceLookupRequest(BaseModel):
    """Request to lookup pricing."""
    
    service: str = Field(..., description="AWS service")
    region: str = Field(..., description="AWS region")
    resource_type: str = Field(..., description="Resource type")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Resource attributes for matching")
    
    class Config:
        json_schema_extra = {
            "example": {
                "service": "ec2",
                "region": "us-east-1",
                "resource_type": "instance",
                "attributes": {
                    "instanceType": "t3.micro",
                    "operatingSystem": "Linux",
                    "tenancy": "Shared"
                }
            }
        }


class PriceLookupResponse(BaseModel):
    """Response from pricing lookup."""
    
    prices: List[NormalizedPrice] = Field(..., description="Matching price records")
    confidence_level: ConfidenceLevel = Field(..., description="Confidence in pricing data")
    metadata: Optional[PricingMetadata] = Field(None, description="Pricing metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prices": [],
                "confidence_level": "HIGH",
                "metadata": {
                    "service": "ec2",
                    "version": "20240101000000",
                    "publication_date": "2024-01-01T00:00:00Z",
                    "last_updated": "2024-01-01T00:00:00Z",
                    "source": "AWS Price List API",
                    "total_skus": 150000
                }
            }
        }
