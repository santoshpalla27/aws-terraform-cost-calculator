"""RDS usage model."""

from typing import Dict, Any, List


class RDSUsageModel:
    """RDS resource usage model."""
    
    def calculate_usage(
        self,
        resource: Dict[str, Any],
        profile: Any,
        overrides: Dict[str, Any] = None
    ) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Calculate RDS usage."""
        assumptions = []
        
        uptime_hours = profile.defaults.get("rds_uptime_hours", 730)
        assumptions.append({
            "parameter": "uptime_hours_per_month",
            "value": uptime_hours,
            "source": f"profile:{profile.profile_name}",
            "description": "Database uptime hours"
        })
        
        storage_gb = profile.defaults.get("rds_storage_gb", 100)
        assumptions.append({
            "parameter": "storage_gb",
            "value": storage_gb,
            "source": f"profile:{profile.profile_name}",
            "description": "Database storage size"
        })
        
        backup_retention = profile.defaults.get("rds_backup_retention_days", 7)
        assumptions.append({
            "parameter": "backup_retention_days",
            "value": backup_retention,
            "source": f"profile:{profile.profile_name}",
            "description": "Backup retention period"
        })
        
        # Apply overrides
        if overrides:
            for key, value in overrides.items():
                if key == "uptime_hours_per_month":
                    uptime_hours = value
                    assumptions.append({
                        "parameter": key,
                        "value": value,
                        "source": "override",
                        "description": "User-provided override"
                    })
        
        usage = {
            "compute_hours": uptime_hours,
            "storage_gb_month": storage_gb,
            "backup_storage_gb_month": storage_gb * backup_retention,
        }
        
        return usage, assumptions
