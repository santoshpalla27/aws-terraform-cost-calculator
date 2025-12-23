"""
NRG (Normalized Resource Graph) builder.
Main orchestrator for plan interpretation.
"""
from typing import Dict, Any, List
from datetime import datetime
from app.schemas.nrg import (
    NormalizedResourceGraph,
    NRGNode,
    InterpretationMetadata,
    ConfidenceLevel
)
from app.interpreter.utils import (
    generate_resource_id,
    compute_plan_hash,
    extract_provider_from_type,
    is_value_unknown
)
from app.interpreter.multiplicity import (
    resolve_multiplicity,
    extract_module_path,
    calculate_module_depth
)
from app.interpreter.dependencies import build_dependency_graph
from app.utils.logger import get_logger

logger = get_logger(__name__)


class NRGBuilder:
    """Builds Normalized Resource Graph from Terraform plan."""
    
    def __init__(self, plan_json: Dict[str, Any]):
        self.plan_json = plan_json
        self.nodes: List[NRGNode] = []
        self.resources_by_type: Dict[str, int] = {}
        self.unknown_count = 0
        self.max_module_depth = 0
        self.address_to_id: Dict[str, str] = {}  # Map Terraform addresses to resource IDs
        self.dependency_graph: Dict[str, List[str]] = {}
    
    def build(self) -> NormalizedResourceGraph:
        """
        Build complete NRG from plan JSON.
        
        Returns:
            NormalizedResourceGraph
        """
        logger.info("Starting NRG build")
        
        # Extract resources from plan
        resources = self._extract_resources()
        
        logger.info(f"Found {len(resources)} resources in plan")
        
        # Process each resource (creates nodes and address-to-ID mapping)
        for resource in resources:
            self._process_resource(resource)
        
        # Extract dependencies from resource_changes
        self.dependency_graph = build_dependency_graph(
            self.plan_json,
            self.address_to_id
        )
        
        # Update nodes with dependencies
        self._apply_dependencies()
        
        # Build metadata
        total_dependencies = sum(len(deps) for deps in self.dependency_graph.values())
        
        metadata = InterpretationMetadata(
            plan_hash=compute_plan_hash(self.plan_json),
            total_resources=len(self.nodes),
            resources_by_type=self.resources_by_type,
            unknown_value_count=self.unknown_count,
            module_depth=self.max_module_depth,
            interpretation_timestamp=datetime.utcnow()
        )
        
        logger.info(
            f"NRG build complete: {len(self.nodes)} nodes, {total_dependencies} dependencies",
            extra={
                'total_resources': len(self.nodes),
                'resources_by_type': self.resources_by_type,
                'unknown_count': self.unknown_count,
                'total_dependencies': total_dependencies
            }
        )
        
        return NormalizedResourceGraph(
            nodes=self.nodes,
            metadata=metadata
        )
    
    def _extract_resources(self) -> List[Dict[str, Any]]:
        """Extract resources from plan JSON."""
        resources = []
        
        # Get planned values
        planned_values = self.plan_json.get('planned_values', {})
        root_module = planned_values.get('root_module', {})
        
        # Extract from root module
        resources.extend(root_module.get('resources', []))
        
        # Extract from child modules recursively
        resources.extend(self._extract_from_modules(root_module.get('child_modules', [])))
        
        return resources
    
    def _extract_from_modules(self, modules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Recursively extract resources from modules."""
        resources = []
        
        for module in modules:
            resources.extend(module.get('resources', []))
            # Recurse into child modules
            resources.extend(self._extract_from_modules(module.get('child_modules', [])))
        
        return resources
    
    def _process_resource(self, resource: Dict[str, Any]) -> None:
        """Process a single resource into NRG node(s)."""
        # Resolve multiplicity (count/for_each)
        instances = resolve_multiplicity(resource)
        
        for instance in instances:
            node = self._build_node(instance)
            self.nodes.append(node)
            
            # Build address-to-ID mapping for dependency resolution
            self.address_to_id[node.terraform_address] = node.resource_id
            
            # Update statistics
            resource_type = node.resource_type
            self.resources_by_type[resource_type] = \
                self.resources_by_type.get(resource_type, 0) + 1
    
    def _build_node(self, instance: Dict[str, Any]) -> NRGNode:
        """Build a single NRG node from resource instance."""
        full_address = instance['full_address']
        resource_type = instance['type']
        values = instance.get('values', {})
        
        # Generate deterministic resource ID
        resource_id = generate_resource_id(full_address)
        
        # Extract provider
        provider = extract_provider_from_type(resource_type)
        
        # Extract module path
        module_path = extract_module_path(full_address)
        
        # Update max module depth
        depth = calculate_module_depth(module_path)
        if depth > self.max_module_depth:
            self.max_module_depth = depth
        
        # Extract attributes and unknowns
        attributes, unknown_attributes = self._extract_attributes(values)
        
        # Update unknown count
        self.unknown_count += len(unknown_attributes)
        
        # Calculate confidence level
        confidence = self._calculate_confidence(attributes, unknown_attributes)
        
        # Extract region (explicit only, no heuristics)
        region = attributes.get('region')
        
        # Dependencies will be populated later
        dependencies = []
        
        return NRGNode(
            resource_id=resource_id,
            terraform_address=full_address,
            resource_type=resource_type,
            provider=provider,
            region=region,
            attributes=attributes,
            unknown_attributes=unknown_attributes,
            quantity=1,
            module_path=module_path,
            dependencies=dependencies,
            confidence_level=confidence
        )
    
    def _extract_attributes(self, values: Dict[str, Any]) -> tuple:
        """
        Extract known and unknown attributes.
        
        Returns:
            (attributes, unknown_attributes)
        """
        attributes = {}
        unknown_attributes = []
        
        for key, value in values.items():
            if is_value_unknown(value):
                unknown_attributes.append(key)
            else:
                attributes[key] = value
        
        return attributes, unknown_attributes
    
    def _calculate_confidence(
        self,
        attributes: Dict[str, Any],
        unknown_attributes: List[str]
    ) -> ConfidenceLevel:
        """Calculate confidence level based on known/unknown ratio."""
        total = len(attributes) + len(unknown_attributes)
        
        if total == 0:
            return ConfidenceLevel.LOW
        
        known_ratio = len(attributes) / total
        
        if known_ratio >= 0.9:
            return ConfidenceLevel.HIGH
        elif known_ratio >= 0.5:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def _apply_dependencies(self) -> None:
        """Apply dependencies to nodes from dependency graph."""
        for node in self.nodes:
            if node.resource_id in self.dependency_graph:
                node.dependencies = self.dependency_graph[node.resource_id]


def interpret_plan(plan_json: Dict[str, Any]) -> NormalizedResourceGraph:
    """
    Main entry point for plan interpretation.
    
    Args:
        plan_json: Terraform plan JSON (from terraform show -json)
        
    Returns:
        NormalizedResourceGraph
    """
    builder = NRGBuilder(plan_json)
    return builder.build()
