"""NAT Gateway metadata resolver."""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class NATResolver:
    """Resolves NAT Gateway metadata."""
    
    def resolve(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve NAT Gateway metadata.
        
        Args:
            resource: NRG resource
            
        Returns:
            Enriched metadata
        """
        # NAT Gateway characteristics (from AWS documentation)
        metadata = {
            "bandwidth_gbps": 45,  # Up to 45 Gbps
            "data_processing_charged": True,  # Charged per GB processed
            "hourly_charge": True,  # Hourly charge applies
            "high_availability": False,  # Single AZ by default
            "connection_tracking": True,  # Tracks connections
            "max_connections": 55_000,  # Per destination
            "idle_timeout_seconds": 350,  # Default idle timeout
            "supports_tcp_udp_icmp": True
        }
        
        # Check if connectivity type is specified
        connectivity_type = resource.get("attributes", {}).get("connectivity_type", "public")
        metadata["connectivity_type"] = connectivity_type
        
        # Private NAT gateways don't charge for data processing
        if connectivity_type == "private":
            metadata["data_processing_charged"] = False
        
        return metadata
