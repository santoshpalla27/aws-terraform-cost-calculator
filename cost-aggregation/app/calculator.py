"""Cost calculator - pure computation engine."""

import logging
from typing import Dict, Any
from decimal import Decimal

from .schema import ResourceCost, CostDriver

logger = logging.getLogger(__name__)


class CostCalculator:
    """Calculates resource costs using formula: cost = usage × pricing."""
    
    def calculate_resource_cost(
        self,
        resource: Dict[str, Any],
        pricing: Dict[str, Any],
        usage: Dict[str, Any],
        profile: str = "prod"
    ) -> ResourceCost:
        """Calculate cost for a single resource.
        
        Args:
            resource: Enriched resource data
            pricing: Pricing data from pricing engine
            usage: Usage data from usage modeling engine
            profile: Usage profile name
            
        Returns:
            Resource cost breakdown
        """
        resource_id = resource.get("resource_id", "unknown")
        resource_type = resource.get("resource_type", "unknown")
        service = self._extract_service(resource_type)
        region = resource.get("region", "unknown")
        
        # Calculate cost components
        compute_cost = self._calculate_compute_cost(usage, pricing)
        storage_cost = self._calculate_storage_cost(usage, pricing)
        network_cost = self._calculate_network_cost(usage, pricing)
        other_cost = self._calculate_other_cost(usage, pricing)
        
        total_cost = compute_cost + storage_cost + network_cost + other_cost
        
        # Calculate confidence
        confidence = self._calculate_confidence(resource, pricing, usage)
        
        # Create resource cost
        resource_cost = ResourceCost(
            resource_id=resource_id,
            resource_type=resource_type,
            service=service,
            region=region,
            compute_cost=compute_cost,
            storage_cost=storage_cost,
            network_cost=network_cost,
            other_cost=other_cost,
            total_monthly_cost=total_cost,
            usage_profile=profile,
            confidence_score=confidence,
            assumptions=usage.get("assumptions", [])
        )
        
        # Identify cost drivers
        resource_cost.cost_drivers = self._identify_cost_drivers(resource_cost)
        
        return resource_cost
    
    def _calculate_compute_cost(self, usage: Dict[str, Any], pricing: Dict[str, Any]) -> Decimal:
        """Calculate compute costs."""
        compute_hours = Decimal(str(usage.get("compute_hours", 0)))
        price_per_hour = Decimal(str(pricing.get("price_per_unit", 0)))
        
        return compute_hours * price_per_hour
    
    def _calculate_storage_cost(self, usage: Dict[str, Any], pricing: Dict[str, Any]) -> Decimal:
        """Calculate storage costs."""
        storage_gb_month = Decimal(str(usage.get("storage_gb_month", 0)))
        ebs_storage_gb_month = Decimal(str(usage.get("ebs_storage_gb_month", 0)))
        backup_storage_gb_month = Decimal(str(usage.get("backup_storage_gb_month", 0)))
        
        storage_rate = Decimal(str(pricing.get("storage_rate", 0)))
        
        total_storage = storage_gb_month + ebs_storage_gb_month + backup_storage_gb_month
        return total_storage * storage_rate
    
    def _calculate_network_cost(self, usage: Dict[str, Any], pricing: Dict[str, Any]) -> Decimal:
        """Calculate network costs."""
        network_out_gb = Decimal(str(usage.get("network_out_gb", 0)))
        data_transfer_rate = Decimal(str(pricing.get("data_transfer_rate", 0)))
        
        return network_out_gb * data_transfer_rate
    
    def _calculate_other_cost(self, usage: Dict[str, Any], pricing: Dict[str, Any]) -> Decimal:
        """Calculate other costs (requests, IOPS, etc.)."""
        requests_get = Decimal(str(usage.get("requests_get", 0)))
        requests_put = Decimal(str(usage.get("requests_put", 0)))
        
        request_rate_get = Decimal(str(pricing.get("request_rate_get", 0)))
        request_rate_put = Decimal(str(pricing.get("request_rate_put", 0)))
        
        return (requests_get * request_rate_get) + (requests_put * request_rate_put)
    
    def _calculate_confidence(
        self,
        resource: Dict[str, Any],
        pricing: Dict[str, Any],
        usage: Dict[str, Any]
    ) -> float:
        """Calculate confidence score."""
        scores = []
        
        # Metadata confidence
        metadata_status = resource.get("metadata_status", {})
        if metadata_status.get("enriched"):
            scores.append(0.9)
        elif metadata_status.get("degraded"):
            scores.append(0.5)
        else:
            scores.append(0.7)
        
        # Pricing confidence
        if pricing.get("sku"):
            scores.append(0.95)
        else:
            scores.append(0.6)
        
        # Usage confidence
        if usage.get("assumptions"):
            scores.append(0.8)
        else:
            scores.append(0.6)
        
        return sum(scores) / len(scores) if scores else 0.5
    
    def _identify_cost_drivers(self, resource_cost: ResourceCost) -> list[CostDriver]:
        """Identify top cost drivers."""
        components = {
            "compute": resource_cost.compute_cost,
            "storage": resource_cost.storage_cost,
            "network": resource_cost.network_cost,
            "other": resource_cost.other_cost
        }
        
        total = resource_cost.total_monthly_cost
        drivers = []
        
        for component, cost in sorted(components.items(), key=lambda x: x[1], reverse=True):
            if cost > 0:
                percentage = float((cost / total * 100) if total > 0 else 0)
                drivers.append(CostDriver(
                    component=component,
                    cost=cost,
                    percentage=round(percentage, 2),
                    description=f"{component.capitalize()} costs"
                ))
        
        return drivers
    
    def _extract_service(self, resource_type: str) -> str:
        """Extract service name from resource type."""
        # Map resource types to services
        service_map = {
            "aws_instance": "EC2",
            "aws_s3_bucket": "S3",
            "aws_db_instance": "RDS",
            "aws_lb": "ELB",
            "aws_nat_gateway": "NAT Gateway",
            "aws_eks_cluster": "EKS",
        }
        
        return service_map.get(resource_type, "Unknown")
