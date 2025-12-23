"""
Cost diff calculator for analyzing cost deltas.
"""
from decimal import Decimal
from app.schemas.cost import CostScenario, CostDiff
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DiffCalculator:
    """Calculates cost differences and spreads."""
    
    @staticmethod
    def calculate_diff(scenario: CostScenario) -> CostDiff:
        """
        Calculate cost diffs from scenario.
        
        Args:
            scenario: Cost scenario
            
        Returns:
            Cost diff with absolute and percentage diffs
        """
        # Absolute diffs
        expected_minus_min = scenario.expected - scenario.min
        max_minus_expected = scenario.max - scenario.expected
        max_minus_min = scenario.max - scenario.min
        
        # Percentage diffs (handle division by zero)
        if scenario.min > 0:
            expected_minus_min_pct = (expected_minus_min / scenario.min) * Decimal('100')
        else:
            expected_minus_min_pct = Decimal('0')
        
        if scenario.expected > 0:
            max_minus_expected_pct = (max_minus_expected / scenario.expected) * Decimal('100')
            scenario_spread = max_minus_min / scenario.expected
        else:
            max_minus_expected_pct = Decimal('0')
            scenario_spread = Decimal('0')
        
        return CostDiff(
            expected_minus_min=expected_minus_min,
            max_minus_expected=max_minus_expected,
            max_minus_min=max_minus_min,
            expected_minus_min_pct=expected_minus_min_pct,
            max_minus_expected_pct=max_minus_expected_pct,
            scenario_spread=scenario_spread
        )
