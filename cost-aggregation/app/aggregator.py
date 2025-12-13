"""Cost aggregation logic."""

import logging
from typing import List, Dict
from decimal import Decimal
from collections import defaultdict

from .schema import ResourceCost, ServiceCost, RegionCost, CostEstimate

logger = logging.getLogger(__name__)


class CostAggregator:
    """Aggregates costs by service, region, etc."""
    
    def aggregate(
        self,
        resource_costs: List[ResourceCost],
        profile: str = "prod"
    ) -> CostEstimate:
        """Create complete cost estimate with all aggregations.
        
        Args:
            resource_costs: List of resource costs
            profile: Usage profile name
            
        Returns:
            Complete cost estimate
        """
        # Calculate total
        total_cost = sum(rc.total_monthly_cost for rc in resource_costs)
        
        # Calculate overall confidence (weighted average)
        if resource_costs:
            total_confidence = sum(
                rc.confidence_score * float(rc.total_monthly_cost)
                for rc in resource_costs
            )
            avg_confidence = total_confidence / float(total_cost) if total_cost > 0 else 0.5
        else:
            avg_confidence = 0.0
        
        # Aggregate by service
        by_service = self.aggregate_by_service(resource_costs)
        
        # Aggregate by region
        by_region = self.aggregate_by_region(resource_costs)
        
        return CostEstimate(
            total_monthly_cost=total_cost,
            confidence_score=round(avg_confidence, 2),
            by_resource=resource_costs,
            by_service=by_service,
            by_region=by_region,
            profile=profile
        )
    
    def aggregate_by_service(self, resource_costs: List[ResourceCost]) -> List[ServiceCost]:
        """Aggregate costs by service."""
        by_service = defaultdict(list)
        
        for rc in resource_costs:
            by_service[rc.service].append(rc)
        
        service_costs = []
        for service, resources in sorted(by_service.items()):
            total = sum(rc.total_monthly_cost for rc in resources)
            service_costs.append(ServiceCost(
                service=service,
                total_cost=total,
                resource_count=len(resources),
                resources=resources
            ))
        
        # Sort by cost descending
        service_costs.sort(key=lambda x: x.total_cost, reverse=True)
        
        return service_costs
    
    def aggregate_by_region(self, resource_costs: List[ResourceCost]) -> List[RegionCost]:
        """Aggregate costs by region."""
        by_region = defaultdict(list)
        
        for rc in resource_costs:
            by_region[rc.region].append(rc)
        
        region_costs = []
        for region, resources in sorted(by_region.items()):
            total = sum(rc.total_monthly_cost for rc in resources)
            
            # Group by service within region
            services = defaultdict(Decimal)
            for rc in resources:
                services[rc.service] += rc.total_monthly_cost
            
            region_costs.append(RegionCost(
                region=region,
                total_cost=total,
                resource_count=len(resources),
                services=dict(services)
            ))
        
        # Sort by cost descending
        region_costs.sort(key=lambda x: x.total_cost, reverse=True)
        
        return region_costs
