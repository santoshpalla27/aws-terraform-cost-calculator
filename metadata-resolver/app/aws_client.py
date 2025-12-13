"""AWS SDK client wrapper."""

import logging
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, BotoCoreError
from typing import Optional, Dict, Any

from .config import settings

logger = logging.getLogger(__name__)


class AWSClient:
    """AWS SDK client wrapper with retry logic."""
    
    def __init__(self, region: Optional[str] = None, profile: Optional[str] = None):
        """Initialize AWS client.
        
        Args:
            region: AWS region
            profile: AWS profile name
        """
        self.region = region or settings.aws_region
        self.profile = profile or settings.aws_profile
        
        # Configure boto3 with retry logic
        self.config = Config(
            region_name=self.region,
            retries={
                'max_attempts': 3,
                'mode': 'adaptive'
            },
            connect_timeout=settings.aws_timeout,
            read_timeout=settings.aws_timeout
        )
        
        # Create session
        if self.profile:
            self.session = boto3.Session(profile_name=self.profile, region_name=self.region)
        else:
            self.session = boto3.Session(region_name=self.region)
        
        # Client cache
        self._clients: Dict[str, Any] = {}
        
        logger.info(f"Initialized AWS client for region: {self.region}")
    
    def get_client(self, service_name: str) -> Any:
        """Get boto3 client for a service.
        
        Args:
            service_name: AWS service name (ec2, elb, eks, etc.)
            
        Returns:
            Boto3 client
        """
        if service_name not in self._clients:
            self._clients[service_name] = self.session.client(
                service_name,
                config=self.config
            )
            logger.debug(f"Created {service_name} client")
        
        return self._clients[service_name]
    
    def describe_images(self, image_ids: list) -> Optional[Dict[str, Any]]:
        """Describe EC2 AMIs.
        
        Args:
            image_ids: List of AMI IDs
            
        Returns:
            AMI details or None on error
        """
        try:
            ec2 = self.get_client('ec2')
            response = ec2.describe_images(ImageIds=image_ids)
            return response
        except ClientError as e:
            logger.error(f"Failed to describe images: {e}")
            return None
        except BotoCoreError as e:
            logger.error(f"Boto core error: {e}")
            return None
    
    def describe_instance_types(self, instance_types: list) -> Optional[Dict[str, Any]]:
        """Describe EC2 instance types.
        
        Args:
            instance_types: List of instance type names
            
        Returns:
            Instance type details or None on error
        """
        try:
            ec2 = self.get_client('ec2')
            response = ec2.describe_instance_types(InstanceTypes=instance_types)
            return response
        except ClientError as e:
            logger.error(f"Failed to describe instance types: {e}")
            return None
        except BotoCoreError as e:
            logger.error(f"Boto core error: {e}")
            return None
    
    def describe_load_balancers(self, load_balancer_arns: list) -> Optional[Dict[str, Any]]:
        """Describe load balancers.
        
        Args:
            load_balancer_arns: List of load balancer ARNs
            
        Returns:
            Load balancer details or None on error
        """
        try:
            elbv2 = self.get_client('elbv2')
            response = elbv2.describe_load_balancers(LoadBalancerArns=load_balancer_arns)
            return response
        except ClientError as e:
            logger.error(f"Failed to describe load balancers: {e}")
            return None
        except BotoCoreError as e:
            logger.error(f"Boto core error: {e}")
            return None
    
    def describe_cluster(self, cluster_name: str) -> Optional[Dict[str, Any]]:
        """Describe EKS cluster.
        
        Args:
            cluster_name: Cluster name
            
        Returns:
            Cluster details or None on error
        """
        try:
            eks = self.get_client('eks')
            response = eks.describe_cluster(name=cluster_name)
            return response
        except ClientError as e:
            logger.error(f"Failed to describe cluster: {e}")
            return None
        except BotoCoreError as e:
            logger.error(f"Boto core error: {e}")
            return None


# Global client cache per region
_clients: Dict[str, AWSClient] = {}


def get_aws_client(region: Optional[str] = None) -> AWSClient:
    """Get AWS client for a region.
    
    Args:
        region: AWS region
        
    Returns:
        AWS client instance
    """
    region = region or settings.aws_region
    
    if region not in _clients:
        _clients[region] = AWSClient(region=region)
    
    return _clients[region]
