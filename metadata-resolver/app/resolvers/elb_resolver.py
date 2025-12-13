"""ELB (ALB/NLB) metadata resolver."""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ELBResolver:
    """Resolves ALB/NLB metadata."""
    
    def resolve(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve load balancer metadata.
        
        Args:
            resource: NRG resource
            
        Returns:
            Enriched metadata
        """
        enriched = {}
        
        load_balancer_type = resource.get("attributes", {}).get("load_balancer_type", "application")
        
        if load_balancer_type == "application":
            enriched = self._resolve_alb(resource)
        elif load_balancer_type == "network":
            enriched = self._resolve_nlb(resource)
        
        return enriched
    
    def _resolve_alb(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve ALB metadata.
        
        Args:
            resource: NRG resource
            
        Returns:
            ALB metadata
        """
        # ALB LCU factors (from AWS documentation)
        metadata = {
            "lcu_factors": {
                "new_connections_per_second": 25,
                "active_connections_per_minute": 3000,
                "processed_bytes_per_second": 1_000_000,  # 1 MB/s
                "rule_evaluations_per_second": 1000
            },
            "cross_zone_load_balancing_enabled": True,  # Default for ALB
            "deletion_protection_enabled": resource.get("attributes", {}).get("enable_deletion_protection", False),
            "http2_enabled": resource.get("attributes", {}).get("enable_http2", True),
            "ip_address_type": resource.get("attributes", {}).get("ip_address_type", "ipv4")
        }
        
        return metadata
    
    def _resolve_nlb(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve NLB metadata.
        
        Args:
            resource: NRG resource
            
        Returns:
            NLB metadata
        """
        # NLB NLCU factors (from AWS documentation)
        metadata = {
            "nlcu_factors": {
                "new_connections_per_second": 800,
                "active_connections_per_minute": 100_000,
                "processed_bytes_per_second": 1_000_000  # 1 MB/s
            },
            "cross_zone_load_balancing_enabled": resource.get("attributes", {}).get("enable_cross_zone_load_balancing", False),  # Default false for NLB
            "deletion_protection_enabled": resource.get("attributes", {}).get("enable_deletion_protection", False),
            "ip_address_type": resource.get("attributes", {}).get("ip_address_type", "ipv4")
        }
        
        return metadata
