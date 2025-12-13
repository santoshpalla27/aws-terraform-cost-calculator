"""Storage service for cost estimation results."""

import logging
from typing import Dict, Any
from decimal import Decimal
import uuid

from .database import get_db
from .models import Job, CostResult, ServiceCost, RegionCost

logger = logging.getLogger(__name__)


class ResultsStorage:
    """Stores cost estimation results (immutable)."""
    
    def store_estimate(
        self,
        estimate: Dict[str, Any],
        user_id: str = None,
        terraform_plan_hash: str = None
    ) -> str:
        """Store cost estimate (INSERT-only, immutable).
        
        Args:
            estimate: Cost estimate from aggregation engine
            user_id: Optional user identifier
            terraform_plan_hash: Optional Terraform plan hash
            
        Returns:
            Job ID (UUID as string)
        """
        with get_db() as db:
            # Create job
            job_id = uuid.uuid4()
            job = Job(
                job_id=job_id,
                profile=estimate.get("profile", "unknown"),
                user_id=user_id,
                terraform_plan_hash=terraform_plan_hash,
                total_monthly_cost=Decimal(str(estimate.get("total_monthly_cost", 0))),
                confidence_score=Decimal(str(estimate.get("confidence_score", 0))),
                resource_count=len(estimate.get("by_resource", []))
            )
            db.add(job)
            db.flush()
            
            # Store cost results (immutable)
            for resource in estimate.get("by_resource", []):
                cost_result = CostResult(
                    job_id=job_id,
                    resource_id=resource.get("resource_id"),
                    resource_type=resource.get("resource_type"),
                    service=resource.get("service"),
                    region=resource.get("region"),
                    compute_cost=Decimal(str(resource.get("compute_cost", 0))),
                    storage_cost=Decimal(str(resource.get("storage_cost", 0))),
                    network_cost=Decimal(str(resource.get("network_cost", 0))),
                    other_cost=Decimal(str(resource.get("other_cost", 0))),
                    total_monthly_cost=Decimal(str(resource.get("total_monthly_cost", 0))),
                    confidence_score=Decimal(str(resource.get("confidence_score", 0))),
                    usage_profile=resource.get("usage_profile"),
                    cost_drivers=resource.get("cost_drivers"),
                    assumptions=resource.get("assumptions")
                )
                db.add(cost_result)
            
            # Store service aggregations (denormalized)
            for service in estimate.get("by_service", []):
                service_cost = ServiceCost(
                    job_id=job_id,
                    service=service.get("service"),
                    total_cost=Decimal(str(service.get("total_cost", 0))),
                    resource_count=service.get("resource_count", 0)
                )
                db.add(service_cost)
            
            # Store region aggregations (denormalized)
            for region in estimate.get("by_region", []):
                region_cost = RegionCost(
                    job_id=job_id,
                    region=region.get("region"),
                    total_cost=Decimal(str(region.get("total_cost", 0))),
                    resource_count=region.get("resource_count", 0),
                    services=region.get("services")
                )
                db.add(region_cost)
            
            db.commit()
            
            logger.info(f"Stored estimate: job_id={job_id}, resources={job.resource_count}")
            
            return str(job_id)
