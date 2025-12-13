"""S3 usage model."""

from typing import Dict, Any, List


class S3UsageModel:
    """S3 resource usage model."""
    
    def calculate_usage(
        self,
        resource: Dict[str, Any],
        profile: Any,
        overrides: Dict[str, Any] = None
    ) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Calculate S3 usage."""
        assumptions = []
        
        storage_gb = profile.defaults.get("s3_storage_gb", 100)
        assumptions.append({
            "parameter": "storage_gb",
            "value": storage_gb,
            "source": f"profile:{profile.profile_name}",
            "description": "Average storage size"
        })
        
        requests_get = profile.defaults.get("s3_requests_get", 10000)
        assumptions.append({
            "parameter": "requests_get",
            "value": requests_get,
            "source": f"profile:{profile.profile_name}",
            "description": "GET requests per month"
        })
        
        requests_put = profile.defaults.get("s3_requests_put", 1000)
        assumptions.append({
            "parameter": "requests_put",
            "value": requests_put,
            "source": f"profile:{profile.profile_name}",
            "description": "PUT requests per month"
        })
        
        # Apply overrides
        if overrides:
            for key, value in overrides.items():
                if key in ["storage_gb", "requests_get", "requests_put"]:
                    if key == "storage_gb":
                        storage_gb = value
                    elif key == "requests_get":
                        requests_get = value
                    elif key == "requests_put":
                        requests_put = value
                    
                    assumptions.append({
                        "parameter": key,
                        "value": value,
                        "source": "override",
                        "description": "User-provided override"
                    })
        
        usage = {
            "storage_gb_month": storage_gb,
            "requests_get": requests_get,
            "requests_put": requests_put,
        }
        
        return usage, assumptions
