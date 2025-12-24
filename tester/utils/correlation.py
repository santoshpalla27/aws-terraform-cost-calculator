"""
Correlation ID tracking and management.
"""
from typing import Dict, List
from collections import defaultdict


class CorrelationTracker:
    """Track correlation IDs across requests for debugging."""
    
    def __init__(self):
        """Initialize tracker."""
        self.correlation_ids: List[str] = []
        self.request_map: Dict[str, dict] = {}
        self.error_map: Dict[str, List[str]] = defaultdict(list)
    
    def track(self, correlation_id: str, endpoint: str, method: str, success: bool):
        """
        Track a request.
        
        Args:
            correlation_id: Request correlation ID
            endpoint: API endpoint
            method: HTTP method
            success: Whether request succeeded
        """
        self.correlation_ids.append(correlation_id)
        self.request_map[correlation_id] = {
            'endpoint': endpoint,
            'method': method,
            'success': success
        }
        
        if not success:
            self.error_map[endpoint].append(correlation_id)
    
    def get_failed_requests(self) -> List[Dict]:
        """Get all failed requests."""
        return [
            {
                'correlation_id': cid,
                **details
            }
            for cid, details in self.request_map.items()
            if not details['success']
        ]
    
    def get_error_summary(self) -> Dict[str, int]:
        """Get error count by endpoint."""
        return {
            endpoint: len(cids)
            for endpoint, cids in self.error_map.items()
        }
    
    def print_summary(self):
        """Print tracking summary."""
        print("\n" + "="*60)
        print("CORRELATION ID TRACKING SUMMARY")
        print("="*60)
        print(f"Total requests: {len(self.correlation_ids)}")
        print(f"Failed requests: {len(self.get_failed_requests())}")
        
        if self.error_map:
            print("\nErrors by endpoint:")
            for endpoint, cids in self.error_map.items():
                print(f"  {endpoint}: {len(cids)} errors")
                for cid in cids[:3]:  # Show first 3
                    print(f"    - {cid}")
        
        print("="*60 + "\n")


# Global tracker instance
_tracker = CorrelationTracker()


def track_request(correlation_id: str, endpoint: str, method: str, success: bool):
    """Track a request globally."""
    _tracker.track(correlation_id, endpoint, method, success)


def get_tracker() -> CorrelationTracker:
    """Get global tracker instance."""
    return _tracker


def print_correlation_summary():
    """Print global tracking summary."""
    _tracker.print_summary()
