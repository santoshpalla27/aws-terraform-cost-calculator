from typing import List
from app.services.base import BaseService, CostComponent
from app.models.terraform import TerraformResource, ProjectContext

class EC2Service(BaseService):
    def get_cost_components(self, resource: TerraformResource, context: ProjectContext) -> List[CostComponent]:
        components = []
        
        instance_type = resource.values.get("instance_type", "t3.micro") # Default fallback
        # In real world, we would resolve variable refs here if they were strictly resolved in the Graph
        
        # 1. Compute Cost
        components.append(CostComponent(
            name=f"Compute ({instance_type})",
            unit="hours",
            hourly_quantity=1,
            monthly_quantity=730,
            price_filter={
                "instanceType": instance_type,
                "operatingSystem": "Linux", # Simplified handling
                "tenancy": "Shared",
                "preInstalledSw": "NA",
                "location": "US East (N. Virginia)" # Hardcoded for Phase 4 MVP
            }
        ))
        
        # 2. EBS Block Devices (Root volume)
        # Not handling detailed EBS mapping in this phase, just core compute
        
        return components
