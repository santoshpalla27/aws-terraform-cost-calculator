"""
EC2 instance usage model.
"""
from typing import Dict, Any
from app.usage_models.base import BaseUsageModel
from app.schemas.usage import UsageAnnotation, UsageConfidence
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EC2UsageModel(BaseUsageModel):
    """Usage model for EC2 instances."""
    
    def get_service_name(self) -> str:
        return "ec2"
    
    def apply_usage(
        self,
        resource: Dict[str, Any],
        profile: Dict[str, Any],
        overrides: Dict[str, Any] = None
    ) -> UsageAnnotation:
        """
        Apply EC2 instance usage assumptions.
        
        Args:
            resource: EC2 resource data
            profile: Usage profile
            overrides: Usage overrides
            
        Returns:
            Usage annotation
        """
        overrides = overrides or {}
        
        # Get profile settings for EC2
        ec2_profile = profile.get('ec2', {}).get('instance', {})
        uptime_config = ec2_profile.get('uptime_hours_per_month', {})
        
        # Check for overrides
        has_override = 'instance_hours' in overrides
        
        if has_override:
            # Use override value
            override_val = overrides['instance_hours']
            instance_hours = self._create_scenario(
                min_val=override_val,
                expected_val=override_val,
                max_val=override_val,
                unit="hours"
            )
        else:
            # Use profile values
            instance_hours = self._create_scenario(
                min_val=uptime_config.get('min', 160),
                expected_val=uptime_config.get('expected', 730),
                max_val=uptime_config.get('max', 730),
                unit="hours"
            )
        
        # Determine if usage is deterministic (24x7)
        is_deterministic = instance_hours.expected == 730 and instance_hours.max == 730
        
        # Build assumptions
        assumptions = []
        if has_override:
            assumptions.append(f"Instance hours overridden to {instance_hours.expected}")
        else:
            profile_assumptions = ec2_profile.get('assumptions', [])
            assumptions.extend(profile_assumptions)
        
        # Build usage annotation
        usage_annotation = UsageAnnotation(
            usage_scenarios={
                'instance_hours': instance_hours
            },
            usage_profile=profile.get('name', 'unknown'),
            usage_confidence=self._determine_confidence(has_override, is_deterministic),
            usage_assumptions=assumptions,
            overrides_applied=['instance_hours'] if has_override else []
        )
        
        return usage_annotation
