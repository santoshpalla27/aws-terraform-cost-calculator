"""
Plan JSON loader from storage references.
"""
import json
from pathlib import Path
from typing import Dict, Any
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PlanLoader:
    """Loads Terraform plan JSON from storage references."""
    
    @staticmethod
    def load(plan_json_reference: str) -> Dict[str, Any]:
        """
        Load plan JSON from reference.
        
        Supports:
        - file:// (local filesystem)
        - Future: s3://, http://, etc.
        
        Args:
            plan_json_reference: Storage reference (e.g., "file:///path/to/plan.json")
            
        Returns:
            Plan JSON dict
            
        Raises:
            ValueError: If reference format is invalid
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If JSON is invalid
        """
        logger.info(f"Loading plan from reference: {plan_json_reference}")
        
        if plan_json_reference.startswith('file://'):
            return PlanLoader._load_from_file(plan_json_reference)
        else:
            raise ValueError(
                f"Unsupported reference scheme: {plan_json_reference}. "
                "Supported: file://"
            )
    
    @staticmethod
    def _load_from_file(reference: str) -> Dict[str, Any]:
        """Load plan JSON from local file."""
        # Remove file:// prefix
        file_path = reference.replace('file://', '')
        
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Plan file not found: {file_path}")
        
        logger.debug(f"Reading plan from file: {file_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            plan_json = json.load(f)
        
        logger.info(f"Successfully loaded plan JSON ({path.stat().st_size} bytes)")
        
        return plan_json
