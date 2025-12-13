"""Enrichment service."""

import logging
from typing import Dict, Any, List

from .resolvers import EC2Resolver, ELBResolver, NATResolver, EKSResolver
from .config import settings

logger = logging.getLogger(__name__)


class MetadataEnricher:
    """Enriches NRG resources with AWS metadata."""
    
    # Resource type to resolver mapping
    RESOLVER_MAP = {
        "aws_instance": EC2Resolver,
        "aws_lb": ELBResolver,
        "aws_alb": ELBResolver,
        "aws_elb": ELBResolver,
        "aws_nat_gateway": NATResolver,
        "aws_eks_cluster": EKSResolver,
    }
    
    def __init__(self):
        """Initialize enricher."""
        self.resolvers = {}
        
        # Initialize resolvers
        for resource_type, resolver_class in self.RESOLVER_MAP.items():
            self.resolvers[resource_type] = resolver_class()
        
        logger.info(f"Initialized enricher with {len(self.resolvers)} resolvers")
    
    def enrich(self, nrg: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich NRG with AWS metadata.
        
        Args:
            nrg: Normalized Resource Graph
            
        Returns:
            Enriched NRG
        """
        resources = nrg.get("resources", [])
        enriched_resources = []
        
        for resource in resources:
            enriched_resource = self._enrich_resource(resource)
            enriched_resources.append(enriched_resource)
        
        # Update NRG
        enriched_nrg = nrg.copy()
        enriched_nrg["resources"] = enriched_resources
        
        logger.info(f"Enriched {len(enriched_resources)} resources")
        
        return enriched_nrg
    
    def _enrich_resource(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich a single resource.
        
        Args:
            resource: NRG resource
            
        Returns:
            Enriched resource
        """
        resource_type = resource.get("resource_type")
        provider = resource.get("provider")
        
        # Only enrich AWS resources
        if provider != "aws":
            return self._add_metadata_status(resource, enriched=False, reason="Non-AWS resource")
        
        # Check if we have a resolver for this resource type
        if resource_type not in self.resolvers:
            return self._add_metadata_status(resource, enriched=False, reason="No resolver available")
        
        # Resolve metadata
        try:
            resolver = self.resolvers[resource_type]
            enriched_metadata = resolver.resolve(resource)
            
            if enriched_metadata:
                # Add enriched metadata to resource
                enriched_resource = resource.copy()
                enriched_resource["enriched_metadata"] = enriched_metadata
                return self._add_metadata_status(enriched_resource, enriched=True)
            else:
                # Graceful degradation
                if settings.enable_graceful_degradation:
                    return self._add_metadata_status(resource, enriched=False, reason="Metadata unavailable", degraded=True)
                else:
                    raise Exception("Metadata resolution failed")
        
        except Exception as e:
            logger.error(f"Failed to enrich resource {resource.get('resource_id')}: {e}")
            
            if settings.enable_graceful_degradation:
                return self._add_metadata_status(resource, enriched=False, reason=str(e), degraded=True)
            else:
                raise
    
    def _add_metadata_status(
        self,
        resource: Dict[str, Any],
        enriched: bool,
        reason: str = None,
        degraded: bool = False
    ) -> Dict[str, Any]:
        """Add metadata status to resource.
        
        Args:
            resource: Resource
            enriched: Whether metadata was enriched
            reason: Reason if not enriched
            degraded: Whether degraded
            
        Returns:
            Resource with metadata status
        """
        resource["metadata_status"] = {
            "enriched": enriched,
            "degraded": degraded
        }
        
        if reason:
            resource["metadata_status"]["reason"] = reason
        
        return resource
