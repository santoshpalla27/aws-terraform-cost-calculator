"""Unit conversion utilities."""

from typing import Dict, Any
from decimal import Decimal


# Unit conversion mappings
UNIT_CONVERSIONS = {
    # Time-based
    "Hrs": {"type": "hourly", "multiplier": 1, "normalized": "hour"},
    "Hour": {"type": "hourly", "multiplier": 1, "normalized": "hour"},
    "hours": {"type": "hourly", "multiplier": 1, "normalized": "hour"},
    
    # Storage
    "GB-Mo": {"type": "storage", "multiplier": 1, "normalized": "GB-month"},
    "GB-Month": {"type": "storage", "multiplier": 1, "normalized": "GB-month"},
    "TB-Mo": {"type": "storage", "multiplier": 1024, "normalized": "GB-month"},
    "GB": {"type": "storage_instant", "multiplier": 1, "normalized": "GB"},
    
    # Requests
    "Requests": {"type": "requests", "multiplier": 1, "normalized": "request"},
    "1M requests": {"type": "requests", "multiplier": 1_000_000, "normalized": "request"},
    "10K requests": {"type": "requests", "multiplier": 10_000, "normalized": "request"},
    
    # Data transfer
    "GB": {"type": "data_transfer", "multiplier": 1, "normalized": "GB"},
    "TB": {"type": "data_transfer", "multiplier": 1024, "normalized": "GB"},
    
    # IOPS
    "IOPS": {"type": "iops", "multiplier": 1, "normalized": "IOPS"},
    "IOPS-Mo": {"type": "iops_monthly", "multiplier": 1, "normalized": "IOPS-month"},
}


def normalize_unit(unit: str) -> str:
    """Normalize unit to standard format.
    
    Args:
        unit: Original unit
        
    Returns:
        Normalized unit
    """
    if unit in UNIT_CONVERSIONS:
        return UNIT_CONVERSIONS[unit]["normalized"]
    return unit


def convert_to_hourly(price: Decimal, unit: str) -> Decimal:
    """Convert price to hourly rate.
    
    Args:
        price: Original price
        unit: Original unit
        
    Returns:
        Hourly price
    """
    if unit in ["GB-Mo", "GB-Month"]:
        # Convert GB-Month to hourly
        # Assume 730 hours per month (365 days / 12 months * 24 hours)
        return price / Decimal("730")
    elif unit in ["Hrs", "Hour", "hours"]:
        return price
    else:
        # Cannot convert, return as-is
        return price


def convert_price(price: Decimal, from_unit: str, to_unit: str) -> Decimal:
    """Convert price between units.
    
    Args:
        price: Original price
        from_unit: Source unit
        to_unit: Target unit
        
    Returns:
        Converted price
    """
    if from_unit == to_unit:
        return price
    
    # Get conversion info
    from_info = UNIT_CONVERSIONS.get(from_unit)
    to_info = UNIT_CONVERSIONS.get(to_unit)
    
    if not from_info or not to_info:
        return price
    
    # Check if same type
    if from_info["type"] != to_info["type"]:
        return price
    
    # Convert via multipliers
    base_price = price / Decimal(str(from_info["multiplier"]))
    converted_price = base_price * Decimal(str(to_info["multiplier"]))
    
    return converted_price
