"""EC2 metadata resolver."""

import logging
from typing import Dict, Any, Optional

from ..aws_client import get_aws_client
from ..cache import get_cache
from ..config import settings

logger = logging.getLogger(__name__)


class EC2Resolver:
    """Resolves EC2 instance metadata."""
    
    def __init__(self):
        """Initialize resolver."""
        self.cache = get_cache()
    
    def resolve(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve EC2 instance metadata.
        
        Args:
            resource: NRG resource
            
        Returns:
            Enriched metadata
        """
        enriched = {}
        
        # Get region
        region = resource.get("region") or settings.aws_region
        
        # Resolve AMI metadata (root volume)
        ami_id = resource.get("attributes", {}).get("ami")
        if ami_id:
            ami_metadata = self._resolve_ami(ami_id, region)
            if ami_metadata:
                enriched.update(ami_metadata)
        
        # Resolve instance type metadata
        instance_type = resource.get("attributes", {}).get("instance_type")
        if instance_type:
            instance_metadata = self._resolve_instance_type(instance_type, region)
            if instance_metadata:
                enriched.update(instance_metadata)
        
        return enriched
    
    def _resolve_ami(self, ami_id: str, region: str) -> Optional[Dict[str, Any]]:
        """Resolve AMI metadata.
        
        Args:
            ami_id: AMI ID
            region: AWS region
            
        Returns:
            AMI metadata or None
        """
        # Check cache
        cache_key = f"{region}:ami:{ami_id}"
        cached = self.cache.get("ami", cache_key, settings.cache_ttl_ami)
        if cached:
            return cached
        
        # Fetch from AWS
        try:
            client = get_aws_client(region)
            response = client.describe_images([ami_id])
            
            if not response or "Images" not in response or len(response["Images"]) == 0:
                logger.warning(f"AMI not found: {ami_id}")
                return None
            
            image = response["Images"][0]
            
            # Extract root volume metadata
            metadata = {}
            if "BlockDeviceMappings" in image and len(image["BlockDeviceMappings"]) > 0:
                root_device = image["BlockDeviceMappings"][0]
                if "Ebs" in root_device:
                    ebs = root_device["Ebs"]
                    metadata = {
                        "root_volume_size": ebs.get("VolumeSize", 8),
                        "root_volume_type": ebs.get("VolumeType", "gp3"),
                        "root_volume_iops": ebs.get("Iops"),
                        "root_volume_throughput": ebs.get("Throughput"),
                        "root_volume_encrypted": ebs.get("Encrypted", False)
                    }
            
            # Cache result
            self.cache.set("ami", cache_key, metadata, settings.cache_ttl_ami)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to resolve AMI {ami_id}: {e}")
            return None
    
    def _resolve_instance_type(self, instance_type: str, region: str) -> Optional[Dict[str, Any]]:
        """Resolve instance type metadata.
        
        Args:
            instance_type: Instance type (e.g., t3.medium)
            region: AWS region
            
        Returns:
            Instance type metadata or None
        """
        # Check cache
        cache_key = f"{region}:instance_type:{instance_type}"
        cached = self.cache.get("instance_type", cache_key, settings.cache_ttl_instance_type)
        if cached:
            return cached
        
        # Fetch from AWS
        try:
            client = get_aws_client(region)
            response = client.describe_instance_types([instance_type])
            
            if not response or "InstanceTypes" not in response or len(response["InstanceTypes"]) == 0:
                logger.warning(f"Instance type not found: {instance_type}")
                return None
            
            instance = response["InstanceTypes"][0]
            
            # Extract metadata
            metadata = {
                "vcpu": instance.get("VCpuInfo", {}).get("DefaultVCpus", 0),
                "memory_mb": instance.get("MemoryInfo", {}).get("SizeInMiB", 0),
                "network_performance": instance.get("NetworkInfo", {}).get("NetworkPerformance", "Unknown"),
                "ebs_optimized_support": instance.get("EbsInfo", {}).get("EbsOptimizedSupport", "unsupported"),
                "ebs_optimized_default": instance.get("EbsInfo", {}).get("EbsOptimizedInfo", {}).get("BaselineBandwidthInMbps", 0),
                "instance_storage": instance.get("InstanceStorageInfo", {}).get("TotalSizeInGB", 0) if "InstanceStorageInfo" in instance else 0,
                "processor": instance.get("ProcessorInfo", {}).get("SupportedArchitectures", [])
            }
            
            # Cache result
            self.cache.set("instance_type", cache_key, metadata, settings.cache_ttl_instance_type)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to resolve instance type {instance_type}: {e}")
            return None
