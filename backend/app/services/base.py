from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.models.terraform import TerraformResource, ProjectContext

class CostComponent(BaseModel):
    name: str
    unit: str
    hourly_quantity: float = 0.0
    monthly_quantity: float = 0.0
    price_filter: Dict[str, Any] # Filters passed to PricingService
    price_estimate: Optional[Dict] = None

class BaseService:
    def get_cost_components(self, resource: TerraformResource, context: ProjectContext) -> List[CostComponent]:
        """
        Derive cost components from a Terraform Resource.
        """
        raise NotImplementedError
