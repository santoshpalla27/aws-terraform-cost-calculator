"""
Deterministic resource ID generation and utilities.
"""
import hashlib
import json
from typing import Any, Dict


def generate_resource_id(terraform_address: str) -> str:
    """
    Generate deterministic resource ID from Terraform address.
    
    Args:
        terraform_address: Full Terraform address
        
    Returns:
        Deterministic 16-character hex ID
    """
    return hashlib.sha256(terraform_address.encode()).hexdigest()[:16]


def compute_plan_hash(plan_json: Dict[str, Any]) -> str:
    """
    Compute deterministic hash of plan JSON.
    
    Args:
        plan_json: Terraform plan JSON
        
    Returns:
        SHA256 hash
    """
    # Serialize to canonical JSON
    canonical = json.dumps(plan_json, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def extract_provider_from_type(resource_type: str) -> str:
    """
    Extract provider from resource type.
    
    Args:
        resource_type: e.g., "aws_instance", "azurerm_virtual_machine"
        
    Returns:
        Provider name (e.g., "aws", "azurerm")
    """
    # Resource types are typically provider_resourcetype
    parts = resource_type.split('_', 1)
    return parts[0] if len(parts) > 1 else "unknown"


def is_value_unknown(value: Any) -> bool:
    """
    Check if a value is unknown/computed.
    
    In Terraform plan JSON, unknown values are typically null or marked.
    
    Args:
        value: Attribute value
        
    Returns:
        True if unknown
    """
    return value is None
