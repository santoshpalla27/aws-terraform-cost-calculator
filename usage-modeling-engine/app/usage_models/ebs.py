"""
EBS volume usage model.
"""
from typing import Dict, Any
from app.usage_models.base import BaseUsageModel
from app.schemas.usage import UsageAnnotation, UsageConfidence
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EBSUsageModel(BaseUsageModel):
    """Usage model for EBS volumes."""
    
    def get_service_name(self) -> str:
        return "ebs"
    
    def apply_usage(
        self,
        resource: Dict[str, Any],
        profile: Dict[str, Any],
        overrides: Dict[str, Any] = None
    ) -> UsageAnnotation:
        """
        Apply EBS volume usage assumptions.
        
        Args:
            resource: EBS resource data
            profile: Usage profile
            overrides: Usage overrides
            
        Returns:
            Usage annotation
        """
        overrides = overrides or {}
        
        # Get profile settings for EBS
        ebs_profile = profile.get('ebs', {}).get('volume', {})
        
        # Get storage size from resource attributes
        storage_gb = resource.get('attributes', {}).get('size', 100)
        
        # Check for overrides
        has_override = 'storage_gb_month' in overrides
        
        if has_override:
            override_val = overrides['storage_gb_month']
            storage_scenario = self._create_scenario(
                min_val=override_val,
                expected_val=override_val,
                max_val=override_val,
                unit="GB-Month"
            )
        else:
            # EBS storage is always full month
            multiplier = ebs_profile.get('storage_gb_month', {}).get('multiplier', 1.0)
            storage_scenario = self._create_scenario(
                min_val=storage_gb * multiplier,
                expected_val=storage_gb * multiplier,
                max_val=storage_gb * multiplier,
                unit="GB-Month"
            )
        
        # Build assumptions
        assumptions = []
        if has_override:
            assumptions.append(f"Storage GB-Month overridden to {storage_scenario.expected}")
        else:
            profile_assumptions = ebs_profile.get('assumptions', [])
            assumptions.extend(profile_assumptions)
        
        # EBS storage is deterministic (always full month)
        is_deterministic = True
        
        # Build usage annotation
        usage_annotation = UsageAnnotation(
            usage_scenarios={
                'storage_gb_month': storage_scenario
            },
            usage_profile=profile.get('name', 'unknown'),
            usage_confidence=self._determine_confidence(has_override, is_deterministic),
            usage_assumptions=assumptions,
            overrides_applied=['storage_gb_month'] if has_override else []
        )
        
        return usage_annotation
