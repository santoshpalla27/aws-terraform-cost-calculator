"""
AWS client manager with STS AssumeRole support.
"""
import boto3
from botocore.config import Config
from typing import Dict, Any
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AWSClientManager:
    """Manages AWS clients with short-lived credentials."""
    
    def __init__(self, role_arn: str = "", region: str = "us-east-1"):
        """
        Initialize AWS client manager.
        
        Args:
            role_arn: IAM role ARN to assume (optional)
            region: Default AWS region
        """
        self.role_arn = role_arn
        self.region = region
        self._session: Dict[str, Any] = {}
        self._clients: Dict[str, Any] = {}
        
        # Boto3 config with retries disabled (we handle retries ourselves)
        self.boto_config = Config(
            region_name=region,
            retries={'max_attempts': 0}
        )
    
    def _get_credentials(self) -> Dict[str, str]:
        """
        Get AWS credentials via STS AssumeRole.
        
        Returns:
            Dict with AccessKeyId, SecretAccessKey, SessionToken
        """
        if not self.role_arn:
            logger.info("No role ARN provided, using default credentials")
            return {}
        
        logger.info(f"Assuming role: {self.role_arn}")
        
        sts = boto3.client('sts')
        response = sts.assume_role(
            RoleArn=self.role_arn,
            RoleSessionName='terraform-cost-calculator-metadata-resolver',
            DurationSeconds=900  # 15 minutes
        )
        
        credentials = response['Credentials']
        logger.info("Successfully assumed role")
        
        return {
            'aws_access_key_id': credentials['AccessKeyId'],
            'aws_secret_access_key': credentials['SecretAccessKey'],
            'aws_session_token': credentials['SessionToken']
        }
    
    def get_client(self, service: str, region: str = None) -> Any:
        """
        Get boto3 client for AWS service.
        
        Args:
            service: AWS service name (ec2, rds, etc.)
            region: AWS region (uses default if not specified)
            
        Returns:
            Boto3 client
        """
        region = region or self.region
        client_key = f"{service}:{region}"
        
        if client_key in self._clients:
            return self._clients[client_key]
        
        # Get credentials
        credentials = self._get_credentials()
        
        # Create client
        if credentials:
            client = boto3.client(
                service,
                config=self.boto_config.merge(Config(region_name=region)),
                **credentials
            )
        else:
            client = boto3.client(
                service,
                config=self.boto_config.merge(Config(region_name=region))
            )
        
        self._clients[client_key] = client
        logger.debug(f"Created {service} client for region {region}")
        
        return client
    
    def clear_clients(self) -> None:
        """Clear all cached clients (forces credential refresh)."""
        self._clients.clear()
        logger.info("Cleared all AWS clients")
