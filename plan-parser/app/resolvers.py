"""Resolvers for count, for_each, conditionals, and modules."""

from typing import List, Dict, Any, Optional
import re


class CountResolver:
    """Resolves count meta-argument."""
    
    @staticmethod
    def resolve(
        address: str,
        count: Optional[int],
        values: Dict[str, Any]
    ) -> List[tuple[str, Dict[str, Any]]]:
        """Resolve count into individual resources.
        
        Args:
            address: Resource address
            count: Count value
            values: Resource values
            
        Returns:
            List of (resource_id, values) tuples
        """
        if count is None or count <= 0:
            return [(address, values)]
        
        resources = []
        for i in range(count):
            resource_id = f"{address}[{i}]"
            # Clone values for each instance
            instance_values = values.copy()
            resources.append((resource_id, instance_values))
        
        return resources


class ForEachResolver:
    """Resolves for_each meta-argument."""
    
    @staticmethod
    def resolve(
        address: str,
        for_each: Optional[Dict[str, Any]],
        values: Dict[str, Any]
    ) -> List[tuple[str, Dict[str, Any]]]:
        """Resolve for_each into individual resources.
        
        Args:
            address: Resource address
            for_each: For_each map
            values: Resource values
            
        Returns:
            List of (resource_id, values) tuples
        """
        if not for_each:
            return [(address, values)]
        
        resources = []
        for key in for_each.keys():
            # Escape key for resource ID
            escaped_key = key.replace('"', '\\"')
            resource_id = f'{address}["{escaped_key}"]'
            
            # Clone values for each instance
            instance_values = values.copy()
            # Add for_each key to values if needed
            instance_values["_for_each_key"] = key
            
            resources.append((resource_id, instance_values))
        
        return resources


class ModuleResolver:
    """Resolves module hierarchy."""
    
    @staticmethod
    def extract_module_path(address: str) -> List[str]:
        """Extract module path from resource address.
        
        Args:
            address: Resource address (e.g., module.web.module.app.aws_instance.server)
            
        Returns:
            Module path (e.g., ["root", "web", "app"])
        """
        if not address.startswith("module."):
            return ["root"]
        
        # Split address by dots
        parts = address.split(".")
        
        # Extract module names
        module_path = ["root"]
        i = 0
        while i < len(parts):
            if parts[i] == "module" and i + 1 < len(parts):
                module_path.append(parts[i + 1])
                i += 2
            else:
                break
        
        return module_path
    
    @staticmethod
    def get_resource_name(address: str) -> str:
        """Extract resource name from address.
        
        Args:
            address: Resource address
            
        Returns:
            Resource name (e.g., aws_instance.server)
        """
        # Remove module prefix
        parts = address.split(".")
        
        # Find last resource type and name
        for i in range(len(parts) - 1, 0, -1):
            if parts[i - 1] != "module" and i + 1 <= len(parts):
                # Found resource type
                return f"{parts[i - 1]}.{parts[i]}"
        
        # Fallback
        if len(parts) >= 2:
            return f"{parts[-2]}.{parts[-1]}"
        
        return address


class ConditionalResolver:
    """Resolves conditional resources."""
    
    @staticmethod
    def is_conditional(change: Dict[str, Any]) -> bool:
        """Check if resource is conditional.
        
        Args:
            change: Resource change object
            
        Returns:
            True if conditional
        """
        # Check if resource has count = 0 or for_each = {}
        # These are typically conditional resources that won't be created
        
        # Check actions
        actions = change.get("change", {}).get("actions", [])
        
        # If actions is ["no-op"], it's not being created
        if actions == ["no-op"]:
            return True
        
        # Check if "create" is in actions
        if "create" not in actions:
            return True
        
        return False
