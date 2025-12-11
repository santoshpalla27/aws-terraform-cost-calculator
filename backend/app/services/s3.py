from typing import List
from app.services.base import BaseService, CostComponent
from app.models.terraform import TerraformResource, ProjectContext

class S3Service(BaseService):
    def get_cost_components(self, resource: TerraformResource, context: ProjectContext) -> List[CostComponent]:
        components = []
        
        # S3 storage is Usage-based, not Resource-based.
        # Terraform doesn't tell us how much data is in the bucket.
        # we return 0 quantity, to be filled by Usage file later.
        
        components.append(CostComponent(
            name="Standard Storage",
            unit="GB-Mo",
            hourly_quantity=0,
            monthly_quantity=0, # Needs usage input
            price_filter={
                "storageClass": "General Purpose",
                "location": "US East (N. Virginia)"
            }
        ))
        
        return components
