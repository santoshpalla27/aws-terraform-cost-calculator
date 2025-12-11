from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class TerraformResource(BaseModel):
    """
    Represents a single parsed Terraform resource.
    """
    address: str = Field(..., description="Unique address e.g. aws_instance.web")
    type: str = Field(..., description="Resource type e.g. aws_instance")
    name: str = Field(..., description="Resource name e.g. web")
    provider: str = Field("aws", description="Provider name")
    values: Dict[str, Any] = Field(default_factory=dict, description="Resource attributes")
    file_path: Optional[str] = None
    line_number: Optional[int] = None

class ProjectContext(BaseModel):
    """
    Holds the state of the parsed project.
    """
    resources: Dict[str, TerraformResource] = Field(default_factory=dict)
    variables: Dict[str, Any] = Field(default_factory=dict)
    locals: Dict[str, Any] = Field(default_factory=dict)
    unresolved_variables: List[str] = Field(default_factory=list)
    
    def add_resource(self, resource: TerraformResource):
        self.resources[resource.address] = resource

    def get_resource(self, address: str) -> Optional[TerraformResource]:
        return self.resources.get(address)
