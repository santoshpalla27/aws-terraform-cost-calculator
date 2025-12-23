"""
Scenario calculator for min/expected/max costs.
"""
from decimal import Decimal
from app.schemas.cost import CostScenario
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ScenarioCalculator:
    """Calculates and validates cost scenarios."""
    
    def __init__(self, default_currency: str = "USD"):
        """
        Initialize scenario calculator.
        
        Args:
            default_currency: Default currency
        """
        self.default_currency = default_currency
    
    def create_scenario(
        self,
        min_cost: Decimal,
        expected_cost: Decimal,
        max_cost: Decimal,
        currency: str = None
    ) -> CostScenario:
        """
        Create cost scenario with validation.
        
        Validates: max ≥ expected ≥ min
        
        Args:
            min_cost: Minimum cost
            expected_cost: Expected cost
            max_cost: Maximum cost
            currency: Currency
            
        Returns:
            CostScenario
        """
        # Validate monotonicity
        if not (max_cost >= expected_cost >= min_cost):
            logger.warning(
                f"Invalid scenario: min={min_cost}, expected={expected_cost}, max={max_cost}. "
                "Adjusting to maintain monotonicity."
            )
            
            # Fix by sorting
            values = sorted([min_cost, expected_cost, max_cost])
            min_cost, expected_cost, max_cost = values[0], values[1], values[2]
            
            logger.info(f"Adjusted scenario: min={min_cost}, expected={expected_cost}, max={max_cost}")
        
        return CostScenario(
            min=min_cost,
            expected=expected_cost,
            max=max_cost,
            currency=currency or self.default_currency
        )
    
    def validate_scenario(self, scenario: CostScenario) -> bool:
        """
        Validate scenario monotonicity.
        
        Args:
            scenario: Cost scenario
            
        Returns:
            True if valid
        """
        return scenario.max >= scenario.expected >= scenario.min
