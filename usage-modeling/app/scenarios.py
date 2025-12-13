"""Scenario generator for min/expected/max cost scenarios."""

import logging
from typing import Dict, Any

from .profiles import UsageProfile, ProfileLoader
from .models import EC2UsageModel, S3UsageModel, RDSUsageModel, ELBUsageModel

logger = logging.getLogger(__name__)


class ScenarioGenerator:
    """Generates min/expected/max cost scenarios."""
    
    # Resource type to model mapping
    MODEL_MAP = {
        "aws_instance": EC2UsageModel,
        "aws_s3_bucket": S3UsageModel,
        "aws_db_instance": RDSUsageModel,
        "aws_lb": ELBUsageModel,
    }
    
    def __init__(self):
        """Initialize scenario generator."""
        self.profile_loader = ProfileLoader()
        self.models = {
            resource_type: model_class()
            for resource_type, model_class in self.MODEL_MAP.items()
        }
    
    def generate_scenarios(
        self,
        resource: Dict[str, Any],
        profile_name: str,
        overrides: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate min/expected/max scenarios.
        
        Args:
            resource: Resource data
            profile_name: Profile name
            overrides: Optional overrides
            
        Returns:
            Scenarios dictionary
        """
        # Load profile
        profile = self.profile_loader.get_profile(profile_name)
        if not profile:
            raise ValueError(f"Profile not found: {profile_name}")
        
        # Get resource type
        resource_type = resource.get("resource_type")
        if resource_type not in self.models:
            logger.warning(f"No model for resource type: {resource_type}")
            return {}
        
        model = self.models[resource_type]
        
        # Expected scenario (profile defaults)
        expected_usage, expected_assumptions = model.calculate_usage(
            resource, profile, overrides
        )
        
        # Min scenario (50% of expected)
        min_factor = profile.scaling.get("min_factor", 0.5)
        min_profile = profile.scale(min_factor)
        min_usage, min_assumptions = model.calculate_usage(
            resource, min_profile, overrides
        )
        
        # Max scenario (150% of expected)
        max_factor = profile.scaling.get("max_factor", 1.5)
        max_profile = profile.scale(max_factor)
        max_usage, max_assumptions = model.calculate_usage(
            resource, max_profile, overrides
        )
        
        return {
            "resource_id": resource.get("resource_id"),
            "resource_type": resource_type,
            "profile": profile_name,
            "scenarios": {
                "min": {
                    "usage": min_usage,
                    "assumptions": min_assumptions,
                    "scaling_factor": min_factor
                },
                "expected": {
                    "usage": expected_usage,
                    "assumptions": expected_assumptions,
                    "scaling_factor": 1.0
                },
                "max": {
                    "usage": max_usage,
                    "assumptions": max_assumptions,
                    "scaling_factor": max_factor
                }
            }
        }
