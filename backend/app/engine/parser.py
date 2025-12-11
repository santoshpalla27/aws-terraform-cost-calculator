import os
import json
import hcl2
from typing import Dict, Any, List
from app.models.terraform import ProjectContext, TerraformResource

class BaseParser:
    def parse(self, directory: str) -> ProjectContext:
        raise NotImplementedError

class PlanJSONParser(BaseParser):
    """
    Parses Terraform Plan JSON (high fidelity).
    """
    def parse(self, file_path: str) -> ProjectContext:
        context = ProjectContext()
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Parse planned_values -> root_module -> resources
        root_module = data.get("planned_values", {}).get("root_module", {})
        self._extract_resources(root_module, context)
        return context

    def _extract_resources(self, module: Dict, context: ProjectContext):
        for res in module.get("resources", []):
            resource = TerraformResource(
                address=res.get("address"),
                type=res.get("type"),
                name=res.get("name"),
                values=res.get("values", {}),
                provider=res.get("provider_name", "aws")
            )
            context.add_resource(resource)
        
        # Recurse child modules
        for child in module.get("child_modules", []):
            self._extract_resources(child, context)

class HCLParser(BaseParser):
    """
    Parses raw .tf files using python-hcl2.
    """
    def parse(self, directory: str) -> ProjectContext:
        context = ProjectContext()
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".tf"):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r') as f:
                        try:
                            # hcl2.load returns a dict with top-level keys like 'resource', 'variable'
                            data = hcl2.load(f)
                            self._process_hcl_data(data, context, file_path)
                        except Exception as e:
                            print(f"Error parsing {file_path}: {e}")
        return context

    def _process_hcl_data(self, data: Dict, context: ProjectContext, file_path: str):
        # Process Resources
        for resource_block in data.get("resource", []):
            # hcl2 structure for resource: {type: {name: {attributes}}}
            for res_type, res_dict in resource_block.items():
                for res_name, res_attrs in res_dict.items():
                    address = f"{res_type}.{res_name}"
                    
                    # Handle count/foreach simple expansion (Phase 2 limitation: fixed definition)
                    # Real expansion needs variable evaluation. Here we just take raw attributes.
                    
                    resource = TerraformResource(
                        address=address,
                        type=res_type,
                        name=res_name,
                        values=res_attrs, # Raw HCL attributes
                        file_path=file_path
                    )
                    context.add_resource(resource)
        
        # Process Variables (Basic detection)
        for var_block in data.get("variable", []):
            for var_name, var_attrs in var_block.items():
                if "default" in var_attrs:
                    context.variables[var_name] = var_attrs["default"]
                else:
                    context.unresolved_variables.append(var_name)
