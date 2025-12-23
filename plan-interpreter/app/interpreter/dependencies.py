"""
Dependency extraction from Terraform plan JSON.

Extracts explicit dependencies from resource_changes section.
"""
from typing import Dict, Any, List, Set
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DependencyExtractor:
    """Extracts and resolves resource dependencies from Terraform plan."""
    
    def __init__(self, plan_json: Dict[str, Any]):
        self.plan_json = plan_json
        self.address_to_resource_id: Dict[str, str] = {}
        self.dependency_map: Dict[str, List[str]] = {}
        self.missing_dependencies: Set[str] = set()
    
    def extract_dependencies(
        self,
        address_to_id_map: Dict[str, str]
    ) -> Dict[str, List[str]]:
        """
        Extract dependencies from plan JSON.
        
        Args:
            address_to_id_map: Mapping of Terraform addresses to NRG resource IDs
            
        Returns:
            Dict mapping resource IDs to lists of dependency resource IDs
        """
        self.address_to_resource_id = address_to_id_map
        
        # Extract from resource_changes section
        resource_changes = self.plan_json.get('resource_changes', [])
        
        logger.info(f"Extracting dependencies from {len(resource_changes)} resource changes")
        
        for resource_change in resource_changes:
            self._process_resource_change(resource_change)
        
        # Log statistics
        total_deps = sum(len(deps) for deps in self.dependency_map.values())
        logger.info(
            f"Dependency extraction complete",
            extra={
                'total_dependencies': total_deps,
                'resources_with_dependencies': len(self.dependency_map),
                'missing_references': len(self.missing_dependencies)
            }
        )
        
        if self.missing_dependencies:
            logger.warning(
                f"Found {len(self.missing_dependencies)} missing dependency references",
                extra={'missing_deps': list(self.missing_dependencies)}
            )
        
        return self.dependency_map
    
    def _process_resource_change(self, resource_change: Dict[str, Any]) -> None:
        """Process a single resource change to extract dependencies."""
        address = resource_change.get('address')
        if not address:
            return
        
        # Get depends_on list
        change = resource_change.get('change', {})
        depends_on = change.get('before_depends_on') or change.get('after_depends_on') or []
        
        if not depends_on:
            return
        
        # Resolve dependencies to resource IDs
        resolved_deps = self._resolve_dependencies(address, depends_on)
        
        if resolved_deps:
            # Get resource ID for this address
            resource_id = self.address_to_resource_id.get(address)
            if resource_id:
                self.dependency_map[resource_id] = resolved_deps
    
    def _resolve_dependencies(
        self,
        source_address: str,
        depends_on: List[str]
    ) -> List[str]:
        """
        Resolve Terraform addresses to NRG resource IDs.
        
        Args:
            source_address: Address of the resource with dependencies
            depends_on: List of Terraform addresses this resource depends on
            
        Returns:
            List of NRG resource IDs
        """
        resolved = []
        
        for dep_address in depends_on:
            # Handle indexed resources (count/for_each)
            # depends_on may reference base address or specific instance
            resource_id = self._find_resource_id(dep_address)
            
            if resource_id:
                resolved.append(resource_id)
            else:
                # Log missing dependency
                self.missing_dependencies.add(dep_address)
                logger.debug(
                    f"Dependency not found: {source_address} depends on {dep_address}"
                )
        
        return resolved
    
    def _find_resource_id(self, terraform_address: str) -> str | None:
        """
        Find NRG resource ID for a Terraform address.
        
        Handles both exact matches and base address matches.
        
        Args:
            terraform_address: Terraform resource address
            
        Returns:
            NRG resource ID or None if not found
        """
        # Try exact match first
        if terraform_address in self.address_to_resource_id:
            return self.address_to_resource_id[terraform_address]
        
        # For dependencies on resources with count/for_each,
        # Terraform may reference the base address
        # We need to find all instances and return the first one
        # (or handle this differently based on requirements)
        
        # Try to find any resource that starts with this address
        for addr, res_id in self.address_to_resource_id.items():
            if addr.startswith(terraform_address + '['):
                # Found an instance of this resource
                return res_id
        
        return None


def build_dependency_graph(
    plan_json: Dict[str, Any],
    address_to_id_map: Dict[str, str]
) -> Dict[str, List[str]]:
    """
    Build dependency graph from plan JSON.
    
    Args:
        plan_json: Terraform plan JSON
        address_to_id_map: Mapping of Terraform addresses to NRG resource IDs
        
    Returns:
        Dict mapping resource IDs to dependency resource IDs
    """
    extractor = DependencyExtractor(plan_json)
    return extractor.extract_dependencies(address_to_id_map)
