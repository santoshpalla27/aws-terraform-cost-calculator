from typing import List
from app.services.base import BaseService, CostComponent
from app.models.terraform import TerraformResource, ProjectContext

class LambdaService(BaseService):
    def get_cost_components(self, resource: TerraformResource, context: ProjectContext) -> List[CostComponent]:
        components = []
        
        # Lambda is also Usage-based (Requests + Duration-GB-Seconds).
        
        # Architecture affects price slightly, memory affects duration price.
        arch = "x86_64"
        if "architectures" in resource.values:
            # architectures is a list, e.g. ["arm64"]
            arch_list = resource.values.get("architectures", [])
            if "arm64" in arch_list:
                arch = "Arm64"
        
        # Duration Cost
        components.append(CostComponent(
            name="Duration",
            unit="GB-Seconds",
            hourly_quantity=0,
            monthly_quantity=0, # Needs usage input
            price_filter={
                "group": "AWS-Lambda-Duration",
                # "groupDescription": f"Duration-{arch}", # Group description varies, simplified here
                "location": "US East (N. Virginia)"
            }
        ))
        
        # Requests Cost
        components.append(CostComponent(
            name="Requests",
            unit="Requests",
            hourly_quantity=0,
            monthly_quantity=0, # Needs usage input
            price_filter={
                "group": "AWS-Lambda-Requests",
                "location": "US East (N. Virginia)"
            }
        ))
        
        return components
