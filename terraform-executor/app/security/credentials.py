"""
Credential resolver for secure credential management.
NO raw credentials in HTTP payloads.
"""
import os
import boto3
from typing import Dict, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CredentialResolver:
    """Resolves credential references to actual credentials."""
    
    def resolve(self, credential_reference: Optional[str]) -> Dict[str, str]:
        """
        Resolve credential reference to environment variables.
        
        Args:
            credential_reference: Reference like "assume-role:terraform-readonly"
            
        Returns:
            Dict of environment variables for subprocess
        """
        if not credential_reference:
            logger.info("No credential reference provided, using ambient credentials")
            return {}
        
        # Parse credential reference
        if credential_reference.startswith("assume-role:"):
            role_name = credential_reference.split(":", 1)[1]
            return self._assume_role(role_name)
        
        logger.warning(f"Unknown credential reference type: {credential_reference}")
        return {}
    
    def _assume_role(self, role_name: str) -> Dict[str, str]:
        """
        Assume IAM role and return short-lived credentials.
        
        Args:
            role_name: Role name or ARN
            
        Returns:
            Environment variables with AWS credentials
        """
        try:
            # Construct role ARN if needed
            if not role_name.startswith("arn:"):
                account_id = os.environ.get("AWS_ACCOUNT_ID", "123456789012")
                role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
            else:
                role_arn = role_name
            
            logger.info(f"Assuming role: {role_arn}")
            
            # Assume role
            sts_client = boto3.client('sts')
            response = sts_client.assume_role(
                RoleArn=role_arn,
                RoleSessionName=f"terraform-executor-{os.getpid()}",
                DurationSeconds=900  # 15 minutes
            )
            
            credentials = response['Credentials']
            
            # Return as environment variables
            env_vars = {
                "AWS_ACCESS_KEY_ID": credentials['AccessKeyId'],
                "AWS_SECRET_ACCESS_KEY": credentials['SecretAccessKey'],
                "AWS_SESSION_TOKEN": credentials['SessionToken']
            }
            
            logger.info("Successfully assumed role (credentials will expire in 15 minutes)")
            return env_vars
        
        except Exception as e:
            logger.error(f"Failed to assume role: {str(e)}")
            return {}


# Global credential resolver instance
credential_resolver = CredentialResolver()
