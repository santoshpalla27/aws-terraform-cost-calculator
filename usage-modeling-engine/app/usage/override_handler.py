"""
Override handler for usage overrides.
"""
from typing import Dict, Any, List
from app.schemas.usage import UsageOverride
from app.utils.logger import get_logger

logger = get_logger(__name__)


class OverrideHandler:
    """Handles usage overrides with precedence."""
    
    def __init__(self, overrides: List[UsageOverride]):
        """
        Initialize override handler.
        
        Args:
            overrides: List of usage overrides
        """
        self.overrides = overrides
        self._build_override_index()
    
    def _build_override_index(self) -> None:
        """Build index of overrides for fast lookup."""
        self.global_overrides: Dict[str, UsageOverride] = {}
        self.service_overrides: Dict[str, Dict[str, UsageOverride]] = {}
        self.resource_overrides: Dict[str, Dict[str, UsageOverride]] = {}
        
        for override in self.overrides:
            if override.resource_id:
                # Resource-level override
                if override.resource_id not in self.resource_overrides:
                    self.resource_overrides[override.resource_id] = {}
                self.resource_overrides[override.resource_id][override.dimension] = override
                
            elif override.service:
                # Service-level override
                if override.service not in self.service_overrides:
                    self.service_overrides[override.service] = {}
                self.service_overrides[override.service][override.dimension] = override
                
            else:
                # Global override
                self.global_overrides[override.dimension] = override
        
        logger.info(
            f"Built override index: "
            f"{len(self.resource_overrides)} resource-level, "
            f"{len(self.service_overrides)} service-level, "
            f"{len(self.global_overrides)} global"
        )
    
    def get_overrides_for_resource(
        self,
        resource_id: str,
        service: str
    ) -> Dict[str, Any]:
        """
        Get applicable overrides for a resource.
        
        Precedence (highest to lowest):
        1. Resource-level
        2. Service-level
        3. Global
        
        Args:
            resource_id: Resource ID
            service: Service name
            
        Returns:
            Dict of dimension -> value
        """
        overrides_dict = {}
        
        # Apply global overrides first (lowest precedence)
        for dimension, override in self.global_overrides.items():
            overrides_dict[dimension] = override.value
        
        # Apply service-level overrides (medium precedence)
        if service in self.service_overrides:
            for dimension, override in self.service_overrides[service].items():
                overrides_dict[dimension] = override.value
        
        # Apply resource-level overrides (highest precedence)
        if resource_id in self.resource_overrides:
            for dimension, override in self.resource_overrides[resource_id].items():
                overrides_dict[dimension] = override.value
        
        return overrides_dict
    
    def has_overrides_for_resource(self, resource_id: str, service: str) -> bool:
        """Check if resource has any applicable overrides."""
        return bool(self.get_overrides_for_resource(resource_id, service))
