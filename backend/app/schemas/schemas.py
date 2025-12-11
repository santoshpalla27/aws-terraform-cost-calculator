from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class CostItem(BaseModel):
    name: str
    unit: str
    hourly_quantity: float
    monthly_quantity: float
    price_per_unit: float
    hourly_cost: float
    monthly_cost: float
    currency: str
    attributes: Optional[Dict[str, Any]] = None

class ResourceCost(BaseModel):
    address: str
    type: str
    total_hourly_cost: float
    total_monthly_cost: float
    cost_components: List[CostItem]

class CostEstimateResponse(BaseModel):
    total_hourly_cost: float
    total_monthly_cost: float
    currency: str
    resources: List[ResourceCost]
    unresolved_variables: List[str]
