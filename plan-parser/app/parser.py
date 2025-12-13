"""Main Terraform Plan Parser."""

from typing import Dict, Any, List, Optional
import logging

from .schema import NRG, NRGResource, NRGMetadata
from .extractors import AttributeExtractor
from .confidence import ConfidenceCalculator
from .resolvers import CountResolver, ForEachResolver, ModuleResolver, ConditionalResolver

logger = logging.getLogger(__name__)


class TerraformPlanParser:
    """Parses Terraform plan JSON into Normalized Resource Graph."""
    
    def __init__(self):
        """Initialize parser."""
        self.extractor = AttributeExtractor()
        self.confidence_calc = ConfidenceCalculator()
        self.count_resolver = CountResolver()
        self.foreach_resolver = ForEachResolver()
        self.module_resolver = ModuleResolver()
        self.conditional_resolver = ConditionalResolver()
    
    def parse(self, plan_json: Dict[str, Any]) -> NRG:
        """Parse Terraform plan JSON into NRG.
        
        Args:
            plan_json: Terraform plan JSON from `terraform show -json`
            
        Returns:
            Normalized Resource Graph
        """
        # Extract metadata
        terraform_version = plan_json.get("terraform_version", "unknown")
        format_version = plan_json.get("format_version", "unknown")
        
        # Extract resource changes
        resource_changes = plan_json.get("resource_changes", [])
        
        # Parse resources
        resources = []
        for change in resource_changes:
            # Skip conditional resources that won't be created
            if self.conditional_resolver.is_conditional(change):
                continue
            
            # Parse resource(s) - may expand to multiple due to count/for_each
            parsed_resources = self._parse_resource_change(change)
            resources.extend(parsed_resources)
        
        # Build metadata
        metadata = self._build_metadata(resources)
        
        # Create NRG
        nrg = NRG(
            resources=resources,
            metadata=metadata,
            terraform_version=terraform_version,
            format_version=format_version
        )
        
        logger.info(f"Parsed {len(resources)} resources from plan")
        
        return nrg
    
    def _parse_resource_change(self, change: Dict[str, Any]) -> List[NRGResource]:
        """Parse a single resource change into NRG resources.
        
        Args:
            change: Resource change object
            
        Returns:
            List of NRG resources (may be multiple due to count/for_each)
        """
        # Extract basic info
        address = change.get("address", "")
        resource_type = change.get("type", "")
        provider_name = change.get("provider_name", "")
        mode = change.get("mode", "managed")
        
        # Skip data sources
        if mode == "data":
            return []
        
        # Extract provider
        provider = self.extractor.extract_provider(provider_name)
        
        # Extract change details
        change_obj = change.get("change", {})
        after = change_obj.get("after", {}) or {}
        after_unknown = change_obj.get("after_unknown", {}) or {}
        actions = change_obj.get("actions", [])
        
        # Extract module path
        module_path = self.module_resolver.extract_module_path(address)
        
        # Check for count
        count = after.get("count")
        for_each = after.get("for_each")
        
        # Resolve count/for_each
        if count is not None and isinstance(count, int):
            resolved = self.count_resolver.resolve(address, count, after)
        elif for_each is not None and isinstance(for_each, dict):
            resolved = self.foreach_resolver.resolve(address, for_each, after)
        else:
            resolved = [(address, after)]
        
        # Create NRG resources
        resources = []
        for resource_id, attributes in resolved:
            # Extract region
            region = self.extractor.extract_region(provider, attributes)
            
            # Extract computed attributes
            computed_attrs = self.extractor.extract_computed_attributes(after_unknown)
            
            # Calculate confidence
            confidence = self.confidence_calc.calculate(
                resource_type,
                attributes,
                computed_attrs
            )
            
            # Create resource
            resource = NRGResource(
                resource_id=resource_id,
                resource_type=resource_type,
                provider=provider,
                region=region,
                quantity=1,  # Each resolved resource is quantity 1
                module_path=module_path,
                attributes=attributes,
                computed_attributes=computed_attrs,
                confidence=confidence,
                parent_id=None,  # Will be set in relationship tracking
                children=[],
                metadata={
                    "action": actions[0] if actions else "unknown",
                    "mode": mode
                }
            )
            
            resources.append(resource)
        
        return resources
    
    def _build_metadata(self, resources: List[NRGResource]) -> NRGMetadata:
        """Build metadata from resources.
        
        Args:
            resources: List of NRG resources
            
        Returns:
            NRG metadata
        """
        providers = set()
        regions = set()
        modules = set()
        resource_types = {}
        
        for resource in resources:
            # Collect providers
            if resource.provider:
                providers.add(resource.provider)
            
            # Collect regions
            if resource.region:
                regions.add(resource.region)
            
            # Collect modules
            modules.update(resource.module_path)
            
            # Count resource types
            resource_types[resource.resource_type] = resource_types.get(resource.resource_type, 0) + 1
        
        return NRGMetadata(
            total_resources=len(resources),
            providers=sorted(list(providers)),
            regions=sorted(list(regions)),
            modules=sorted(list(modules)),
            resource_types=resource_types
        )
    
    def track_relationships(self, nrg: NRG) -> NRG:
        """Track parent-child relationships in the graph.
        
        This is a placeholder for relationship tracking logic.
        Can be extended to detect dependencies based on resource references.
        
        Args:
            nrg: Normalized Resource Graph
            
        Returns:
            NRG with relationships tracked
        """
        # TODO: Implement relationship tracking
        # This would involve:
        # 1. Parsing resource attributes for references to other resources
        # 2. Building dependency graph
        # 3. Setting parent_id and children fields
        
        return nrg
