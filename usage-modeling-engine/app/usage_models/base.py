"""
Base usage model interface.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from app.schemas.usage import UsageAnnotation, UsageScenario, UsageConfidence
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BaseUsageModel(ABC):
    """Base class for resource-specific usage models."""
    
    @abstractmethod
    def get_service_name(self) -> str:
        """Get the service name this model handles."""
        pass
    
    @abstractmethod
    def apply_usage(
        self,
        resource: Dict[str, Any],
        profile: Dict[str, Any],
        overrides: Dict[str, Any] = None
    ) -> UsageAnnotation:
        """
        Apply usage assumptions to a resource.
        
        Args:
            resource: Resource data
            profile: Usage profile
            overrides: Usage overrides (optional)
            
        Returns:
            Usage annotation
        """
        pass
    
    def _create_scenario(
        self,
        min_val: float,
        expected_val: float,
        max_val: float,
        unit: str
    ) -> UsageScenario:
        """
        Create usage scenario with validation.
        
        Args:
            min_val: Minimum value
            expected_val: Expected value
            max_val: Maximum value
            unit: Usage unit
            
        Returns:
            Usage scenario
        """
        # Validate: max >= expected >= min
        if not (max_val >= expected_val >= min_val):
            logger.warning(
                f"Invalid scenario values: min={min_val}, expected={expected_val}, max={max_val}. "
                "Adjusting to maintain consistency."
            )
            # Fix by setting expected to average of min and max
            expected_val = (min_val + max_val) / 2
        
        return UsageScenario(
            min=min_val,
            expected=expected_val,
            max=max_val,
            unit=unit
        )
    
    def _determine_confidence(
        self,
        has_override: bool,
        is_deterministic: bool
    ) -> UsageConfidence:
        """
        Determine usage confidence level.
        
        Args:
            has_override: Whether an override was applied
            is_deterministic: Whether usage is deterministic (e.g., 24x7)
            
        Returns:
            Usage confidence level
        """
        if has_override:
            return UsageConfidence.HIGH
        elif is_deterministic:
            return UsageConfidence.HIGH
        else:
            return UsageConfidence.MEDIUM
