"""
Core cost calculator using Decimal arithmetic.
"""
from decimal import Decimal
from typing import Optional
from app.schemas.cost import CostDimension
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CostCalculator:
    """Calculates costs using Decimal arithmetic for financial accuracy."""
    
    def __init__(self, default_currency: str = "USD"):
        """
        Initialize cost calculator.
        
        Args:
            default_currency: Default currency for calculations
        """
        self.default_currency = default_currency
    
    def calculate_cost(
        self,
        dimension: str,
        usage_units: Decimal,
        unit_price: Decimal,
        unit: str,
        currency: Optional[str] = None
    ) -> CostDimension:
        """
        Calculate cost for a single dimension.
        
        Formula: cost = usage_units × unit_price
        
        Args:
            dimension: Pricing dimension name
            usage_units: Usage units (Decimal)
            unit_price: Unit price (Decimal)
            unit: Unit string
            currency: Currency (optional)
            
        Returns:
            CostDimension with calculated cost
        """
        # Validate inputs
        if usage_units < 0:
            logger.warning(f"Negative usage units for {dimension}: {usage_units}, setting to 0")
            usage_units = Decimal('0')
        
        if unit_price < 0:
            logger.warning(f"Negative unit price for {dimension}: {unit_price}, setting to 0")
            unit_price = Decimal('0')
        
        # Calculate cost using Decimal arithmetic
        cost = usage_units * unit_price
        
        logger.debug(
            f"Calculated cost for {dimension}: "
            f"{usage_units} {unit} × ${unit_price} = ${cost}"
        )
        
        return CostDimension(
            dimension=dimension,
            usage_units=usage_units,
            unit_price=unit_price,
            cost=cost,
            unit=unit,
            currency=currency or self.default_currency
        )
    
    def validate_unit_compatibility(self, usage_unit: str, pricing_unit: str) -> bool:
        """
        Validate that usage and pricing units are compatible.
        
        Args:
            usage_unit: Unit from usage model
            pricing_unit: Unit from pricing
            
        Returns:
            True if compatible
        """
        # Normalize units for comparison
        usage_normalized = usage_unit.lower().replace('-', '').replace('_', '')
        pricing_normalized = pricing_unit.lower().replace('-', '').replace('_', '')
        
        # Check if units match
        if usage_normalized == pricing_normalized:
            return True
        
        # Check common aliases
        aliases = {
            'hours': ['hour', 'hrs', 'hr', 'h'],
            'gbmonth': ['gb-month', 'gb_month', 'gbmo'],
            'gb': ['gigabyte', 'gigabytes'],
            'lcuhour': ['lcu-hour', 'lcu_hour', 'lcuhr']
        }
        
        for canonical, variants in aliases.items():
            if usage_normalized in variants and pricing_normalized in variants:
                return True
            if usage_normalized == canonical and pricing_normalized in variants:
                return True
            if pricing_normalized == canonical and usage_normalized in variants:
                return True
        
        logger.warning(
            f"Unit mismatch: usage='{usage_unit}', pricing='{pricing_unit}'. "
            "Proceeding with calculation but results may be incorrect."
        )
        
        return False
