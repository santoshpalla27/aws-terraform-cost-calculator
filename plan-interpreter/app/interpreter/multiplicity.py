"""
Resource multiplicity resolution (count and for_each).
"""
from typing import List, Dict, Any, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)


def build_terraform_address(
    address: str,
    index: Optional[Any] = None
) -> str:
    """
    Build full Terraform address with index.
    
    Args:
        address: Base address (e.g., "aws_instance.web")
        index: Index (int for count, str for for_each)
        
    Returns:
        Full address (e.g., "aws_instance.web[0]" or 'aws_instance.web["prod"]')
    """
    if index is None:
        return address
    
    if isinstance(index, int):
        return f"{address}[{index}]"
    else:
        # for_each key
        return f'{address}["{index}"]'


def resolve_multiplicity(resource: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Resolve resource multiplicity (count/for_each).
    
    Creates ONE node per actual resource instance.
    
    Args:
        resource: Resource from Terraform plan
        
    Returns:
        List of resolved resource instances
    """
    address = resource.get('address', '')
    index = resource.get('index')
    
    # Build full address with index
    full_address = build_terraform_address(address, index)
    
    # Create single instance
    instance = {
        'address': address,
        'full_address': full_address,
        'index': index,
        'values': resource.get('values', {}),
        'type': resource.get('type'),
        'mode': resource.get('mode'),
        'provider_name': resource.get('provider_name')
    }
    
    return [instance]


def extract_module_path(address: str) -> List[str]:
    """
    Extract module path from Terraform address.
    
    Args:
        address: Full Terraform address (e.g., "module.vpc.module.subnets.aws_subnet.private[0]")
        
    Returns:
        Module path list (e.g., ["module.vpc", "module.subnets"])
    """
    parts = address.split('.')
    module_path = []
    
    i = 0
    while i < len(parts):
        if parts[i] == 'module' and i + 1 < len(parts):
            module_path.append(f"module.{parts[i + 1]}")
            i += 2
        else:
            i += 1
    
    return module_path


def calculate_module_depth(module_path: List[str]) -> int:
    """Calculate module nesting depth."""
    return len(module_path)
