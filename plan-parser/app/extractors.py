"""Attribute extractors for different providers."""

from typing import Dict, Any, Optional, List, Tuple


class AttributeExtractor:
    """Extracts attributes from Terraform resources."""
    
    @staticmethod
    def extract_provider(provider_name: str) -> str:
        """Extract provider from provider_name.
        
        Args:
            provider_name: Full provider name (e.g., registry.terraform.io/hashicorp/aws)
            
        Returns:
            Provider short name (e.g., aws)
        """
        if not provider_name:
            return "unknown"
        
        # Extract last part after /
        parts = provider_name.split("/")
        return parts[-1] if parts else "unknown"
    
    @staticmethod
    def extract_region(provider: str, attributes: Dict[str, Any], provider_config: Optional[Dict] = None) -> Optional[str]:
        """Extract region from resource attributes.
        
        Args:
            provider: Provider name
            attributes: Resource attributes
            provider_config: Provider configuration
            
        Returns:
            Region string or None
        """
        # Provider-specific region extraction
        if provider == "aws":
            # Check resource attributes first
            if "region" in attributes:
                return attributes["region"]
            # Check availability_zone
            if "availability_zone" in attributes:
                az = attributes["availability_zone"]
                # Extract region from AZ (e.g., us-east-1a -> us-east-1)
                if isinstance(az, str) and len(az) > 0:
                    return az[:-1] if az[-1].isalpha() else az
            # Check provider config
            if provider_config and "region" in provider_config:
                return provider_config["region"]
        
        elif provider == "azurerm":
            # Azure uses "location"
            if "location" in attributes:
                return attributes["location"]
        
        elif provider == "google":
            # GCP uses zone or region
            if "zone" in attributes:
                return attributes["zone"]
            if "region" in attributes:
                return attributes["region"]
        
        return None
    
    @staticmethod
    def extract_computed_attributes(after_unknown: Dict[str, Any], prefix: str = "") -> List[str]:
        """Extract list of computed attributes from after_unknown.
        
        Args:
            after_unknown: Dictionary of unknown attributes
            prefix: Prefix for nested attributes
            
        Returns:
            List of computed attribute paths
        """
        computed = []
        
        for key, value in after_unknown.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, bool) and value:
                # Simple computed attribute
                computed.append(full_key)
            elif isinstance(value, dict):
                # Nested computed attributes
                nested = AttributeExtractor.extract_computed_attributes(value, full_key)
                computed.extend(nested)
        
        return computed
    
    @staticmethod
    def flatten_attributes(attributes: Dict[str, Any], max_depth: int = 3) -> Dict[str, Any]:
        """Flatten nested attributes for easier processing.
        
        Args:
            attributes: Resource attributes
            max_depth: Maximum nesting depth
            
        Returns:
            Flattened attributes
        """
        # For now, return as-is
        # Can implement flattening if needed for specific use cases
        return attributes
    
    @staticmethod
    def count_attributes(attributes: Dict[str, Any], depth: int = 0, max_depth: int = 3) -> int:
        """Count total number of attributes recursively.
        
        Args:
            attributes: Attributes dictionary
            depth: Current depth
            max_depth: Maximum depth to traverse
            
        Returns:
            Total attribute count
        """
        if depth > max_depth:
            return 0
        
        count = 0
        for key, value in attributes.items():
            count += 1
            if isinstance(value, dict):
                count += AttributeExtractor.count_attributes(value, depth + 1, max_depth)
        
        return count
    
    @staticmethod
    def get_critical_attributes(resource_type: str) -> List[str]:
        """Get list of critical attributes for a resource type.
        
        Args:
            resource_type: Resource type (e.g., aws_instance)
            
        Returns:
            List of critical attribute names
        """
        # Define critical attributes per resource type
        critical_attrs = {
            # AWS
            "aws_instance": ["instance_type", "ami"],
            "aws_db_instance": ["instance_class", "engine", "allocated_storage"],
            "aws_s3_bucket": ["bucket"],
            "aws_ebs_volume": ["size", "type"],
            "aws_elb": ["instances"],
            "aws_lb": ["load_balancer_type"],
            
            # Azure
            "azurerm_virtual_machine": ["vm_size"],
            "azurerm_linux_virtual_machine": ["size"],
            "azurerm_windows_virtual_machine": ["size"],
            "azurerm_sql_database": ["sku_name"],
            
            # GCP
            "google_compute_instance": ["machine_type"],
            "google_sql_database_instance": ["tier"],
        }
        
        return critical_attrs.get(resource_type, [])
