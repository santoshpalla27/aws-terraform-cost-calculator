"""ELB usage model."""

from typing import Dict, Any, List


class ELBUsageModel:
    """ELB resource usage model."""
    
    def calculate_usage(
        self,
        resource: Dict[str, Any],
        profile: Any,
        overrides: Dict[str, Any] = None
    ) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Calculate ELB usage."""
        assumptions = []
        
        uptime_hours = profile.defaults.get("elb_uptime_hours", 730)
        assumptions.append({
            "parameter": "uptime_hours_per_month",
            "value": uptime_hours,
            "source": f"profile:{profile.profile_name}",
            "description": "Load balancer uptime hours"
        })
        
        processed_gb = profile.defaults.get("elb_processed_gb", 100)
        assumptions.append({
            "parameter": "processed_gb",
            "value": processed_gb,
            "source": f"profile:{profile.profile_name}",
            "description": "Data processed per month"
        })
        
        connections_per_sec = profile.defaults.get("elb_connections_per_second", 50)
        assumptions.append({
            "parameter": "connections_per_second",
            "value": connections_per_sec,
            "source": f"profile:{profile.profile_name}",
            "description": "Average connections per second"
        })
        
        # Apply overrides
        if overrides:
            for key, value in overrides.items():
                if key == "processed_gb":
                    processed_gb = value
                    assumptions.append({
                        "parameter": key,
                        "value": value,
                        "source": "override",
                        "description": "User-provided override"
                    })
        
        usage = {
            "uptime_hours": uptime_hours,
            "processed_gb": processed_gb,
            "lcu_hours": uptime_hours,  # Simplified LCU calculation
        }
        
        return usage, assumptions
