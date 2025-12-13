"""Terraform plan diff engine."""

import logging
from typing import Dict, Any
from decimal import Decimal

from .schema import CostEstimate, CostDiff, ResourceCost

logger = logging.getLogger(__name__)


class DiffEngine:
    """Calculates cost differences between before and after states."""
    
    def calculate_diff(
        self,
        before: CostEstimate,
        after: CostEstimate
    ) -> CostDiff:
        """Calculate cost diff between before and after.
        
        Args:
            before: Cost estimate before changes
            after: Cost estimate after changes
            
        Returns:
            Cost difference
        """
        # Create resource maps
        before_resources = {r.resource_id: r for r in before.by_resource}
        after_resources = {r.resource_id: r for r in after.by_resource}
        
        # Find added resources
        added = [
            r for rid, r in after_resources.items()
            if rid not in before_resources
        ]
        added_cost = sum(r.total_monthly_cost for r in added)
        
        # Find removed resources
        removed = [
            r for rid, r in before_resources.items()
            if rid not in after_resources
        ]
        removed_cost = sum(r.total_monthly_cost for r in removed)
        
        # Find changed resources
        changed = []
        for rid in set(before_resources) & set(after_resources):
            before_cost = before_resources[rid].total_monthly_cost
            after_cost = after_resources[rid].total_monthly_cost
            
            if before_cost != after_cost:
                delta = after_cost - before_cost
                changed.append({
                    "resource_id": rid,
                    "resource_type": after_resources[rid].resource_type,
                    "before_cost": float(before_cost),
                    "after_cost": float(after_cost),
                    "delta": float(delta),
                    "percentage_change": float((delta / before_cost * 100) if before_cost > 0 else 0)
                })
        
        # Calculate total delta
        total_delta = after.total_monthly_cost - before.total_monthly_cost
        percentage_change = float(
            (total_delta / before.total_monthly_cost * 100)
            if before.total_monthly_cost > 0 else 0
        )
        
        return CostDiff(
            total_delta=total_delta,
            percentage_change=round(percentage_change, 2),
            added_resources=added,
            removed_resources=removed,
            changed_resources=changed,
            added_cost=added_cost,
            removed_cost=removed_cost
        )
