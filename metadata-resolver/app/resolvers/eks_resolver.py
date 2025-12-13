"""EKS metadata resolver."""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class EKSResolver:
    """Resolves EKS cluster metadata."""
    
    def resolve(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve EKS cluster metadata.
        
        Args:
            resource: NRG resource
            
        Returns:
            Enriched metadata
        """
        # EKS control plane pricing (from AWS documentation)
        metadata = {
            "control_plane_hourly_cost": 0.10,  # $0.10/hour per cluster
            "control_plane_ha": True,  # Multi-AZ by default
            "kubernetes_version": resource.get("attributes", {}).get("version", "1.28"),
            "endpoint_private_access": resource.get("attributes", {}).get("endpoint_private_access", False),
            "endpoint_public_access": resource.get("attributes", {}).get("endpoint_public_access", True),
            "fargate_enabled": False,  # Determined by fargate profiles
            "managed_node_groups": True,  # Supports managed node groups
            "self_managed_nodes": True,  # Supports self-managed nodes
        }
        
        # Check for enabled cluster log types
        enabled_log_types = resource.get("attributes", {}).get("enabled_cluster_log_types", [])
        metadata["logging_enabled"] = len(enabled_log_types) > 0
        metadata["log_types"] = enabled_log_types
        
        # Check for encryption config
        encryption_config = resource.get("attributes", {}).get("encryption_config", [])
        metadata["secrets_encryption_enabled"] = len(encryption_config) > 0
        
        return metadata
