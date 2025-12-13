"""EC2 usage model."""

from typing import Dict, Any, List


class EC2UsageModel:
    """EC2 resource usage model."""
    
    def calculate_usage(
        self,
        resource: Dict[str, Any],
        profile: Any,
        overrides: Dict[str, Any] = None
    ) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Calculate EC2 usage.
        
        Args:
            resource: Resource attributes
            profile: Usage profile
            overrides: Optional overrides
            
        Returns:
            Tuple of (usage, assumptions)
        """
        # Base assumptions from profile
        assumptions = []
        
        uptime_hours = profile.defaults.get("ec2_uptime_hours", 730)
        assumptions.append({
            "parameter": "uptime_hours_per_month",
            "value": uptime_hours,
            "source": f"profile:{profile.profile_name}",
            "description": f"Instance uptime based on {profile.environment} environment"
        })
        
        cpu_util = profile.defaults.get("ec2_cpu_utilization", 50)
        assumptions.append({
            "parameter": "cpu_utilization_percent",
            "value": cpu_util,
            "source": f"profile:{profile.profile_name}",
            "description": f"Average CPU utilization for {profile.environment}"
        })
        
        network_out = profile.defaults.get("ec2_network_out_gb", 100)
        assumptions.append({
            "parameter": "network_out_gb",
            "value": network_out,
            "source": f"profile:{profile.profile_name}",
            "description": "Data transfer out per month"
        })
        
        # Get EBS volume size from resource or profile
        ebs_volume_gb = resource.get("enriched_metadata", {}).get("root_volume_size", 8)
        assumptions.append({
            "parameter": "ebs_volume_gb",
            "value": ebs_volume_gb,
            "source": "resource_metadata",
            "description": "Root EBS volume size"
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
                elif key == "network_out_gb":
                    network_out = value
                    assumptions.append({
                        "parameter": key,
                        "value": value,
                        "source": "override",
                        "description": "User-provided override"
                    })
        
        # Calculate usage
        usage = {
            "compute_hours": uptime_hours,
            "network_out_gb": network_out,
            "ebs_storage_gb_month": ebs_volume_gb,
        }
        
        return usage, assumptions
