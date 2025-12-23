"""
Base service adapter interface.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.schemas.erg import ERGNode


class BaseServiceAdapter(ABC):
    """Abstract base class for AWS service adapters."""
    
    def __init__(self, aws_client_manager, cache, retry_handler):
        """
        Initialize service adapter.
        
        Args:
            aws_client_manager: AWS client manager
            cache: Cache implementation
            retry_handler: Retry handler
        """
        self.aws_client_manager = aws_client_manager
        self.cache = cache
        self.retry_handler = retry_handler
        self.service_name = self._get_service_name()
    
    @abstractmethod
    def _get_service_name(self) -> str:
        """
        Get AWS service name.
        
        Returns:
            Service name (e.g., 'ec2', 'rds')
        """
        pass
    
    @abstractmethod
    async def enrich(self, node: ERGNode, account_id: str) -> ERGNode:
        """
        Enrich a single resource node with AWS metadata.
        
        Args:
            node: ERG node to enrich
            account_id: AWS account ID
            
        Returns:
            Enriched ERG node
        """
        pass
    
    @abstractmethod
    async def detect_implicit_resources(
        self,
        node: ERGNode,
        account_id: str
    ) -> List[ERGNode]:
        """
        Detect implicit billable resources created by this resource.
        
        Args:
            node: Parent ERG node
            account_id: AWS account ID
            
        Returns:
            List of implicit ERG nodes
        """
        pass
    
    def can_handle(self, resource_type: str) -> bool:
        """
        Check if adapter can handle resource type.
        
        Args:
            resource_type: AWS resource type
            
        Returns:
            True if adapter can handle this type
        """
        return resource_type.startswith(f"{self.service_name}_")
