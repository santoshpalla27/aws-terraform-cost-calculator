"""Terraform plan JSON parser."""

import json
from typing import Dict, Any, Optional

from .utils.logger import get_logger

logger = get_logger(__name__)


class PlanParser:
    """Parses Terraform plan JSON output."""
    
    @staticmethod
    def parse_plan_json(json_output: str) -> Optional[Dict[str, Any]]:
        """Parse Terraform plan JSON.
        
        Args:
            json_output: Raw JSON output from terraform show -json
            
        Returns:
            Parsed JSON dict or None if invalid
        """
        try:
            plan_data = json.loads(json_output)
            
            # Validate basic structure
            if not isinstance(plan_data, dict):
                logger.error("Invalid plan JSON: not a dictionary")
                return None
            
            # Check for required fields
            required_fields = ["format_version", "terraform_version"]
            for field in required_fields:
                if field not in plan_data:
                    logger.warning(f"Plan JSON missing field: {field}")
            
            logger.info(
                "Parsed plan JSON",
                format_version=plan_data.get("format_version"),
                terraform_version=plan_data.get("terraform_version")
            )
            
            return plan_data
            
        except json.JSONDecodeError as e:
            logger.error("Failed to parse plan JSON", error=str(e))
            return None
    
    @staticmethod
    def extract_resource_changes(plan_data: Dict[str, Any]) -> list:
        """Extract resource changes from plan.
        
        Args:
            plan_data: Parsed plan JSON
            
        Returns:
            List of resource changes
        """
        return plan_data.get("resource_changes", [])
    
    @staticmethod
    def get_summary(plan_data: Dict[str, Any]) -> Dict[str, int]:
        """Get summary of planned changes.
        
        Args:
            plan_data: Parsed plan JSON
            
        Returns:
            Summary dict with counts
        """
        resource_changes = PlanParser.extract_resource_changes(plan_data)
        
        summary = {
            "create": 0,
            "update": 0,
            "delete": 0,
            "no_change": 0
        }
        
        for change in resource_changes:
            actions = change.get("change", {}).get("actions", [])
            
            if "create" in actions:
                summary["create"] += 1
            elif "update" in actions:
                summary["update"] += 1
            elif "delete" in actions:
                summary["delete"] += 1
            else:
                summary["no_change"] += 1
        
        return summary
