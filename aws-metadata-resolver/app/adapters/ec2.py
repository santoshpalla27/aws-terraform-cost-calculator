"""
EC2 service adapter.
"""
from typing import List, Dict, Any
from app.adapters.base import BaseServiceAdapter
from app.schemas.erg import ERGNode, ResourceProvenance, ConfidenceLevel
from app.cache.interface import generate_cache_key
from app.utils.logger import get_logger
import hashlib

logger = get_logger(__name__)


class EC2Adapter(BaseServiceAdapter):
    """EC2 service adapter for enrichment."""
    
    def _get_service_name(self) -> str:
        return "ec2"
    
    async def enrich(self, node: ERGNode, account_id: str) -> ERGNode:
        """Enrich EC2 instance with AWS metadata."""
        if node.resource_type != "aws_instance":
            return node
        
        logger.info(f"Enriching EC2 instance: {node.terraform_address}")
        
        # Get instance metadata from AWS
        instance_metadata = await self._get_instance_metadata(
            node.attributes.get('instance_type', ''),
            node.region or 'us-east-1',
            account_id
        )
        
        if instance_metadata:
            node.enriched_attributes.update(instance_metadata)
            logger.info(f"Enriched EC2 instance with {len(instance_metadata)} attributes from AWS")
        else:
            logger.warning(f"Could not retrieve AWS metadata for {node.terraform_address}")
        
        return node
    
    async def _get_instance_metadata(
        self,
        instance_type: str,
        region: str,
        account_id: str
    ) -> Dict[str, Any]:
        """
        Get instance metadata from AWS DescribeInstanceTypes API.
        
        Args:
            instance_type: EC2 instance type (e.g., 't3.micro')
            region: AWS region
            account_id: AWS account ID
            
        Returns:
            Dict of instance metadata
        """
        if not instance_type:
            return {}
        
        # Check cache first
        cache_key = generate_cache_key(
            account_id,
            region,
            'ec2',
            'instance_type',
            instance_type
        )
        
        cached = await self.cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for instance type {instance_type}")
            return cached
        
        # Call AWS API
        try:
            ec2_client = self.aws_client_manager.get_client('ec2', region)
            
            response = self.retry_handler.execute_with_retry(
                lambda: ec2_client.describe_instance_types(
                    InstanceTypes=[instance_type]
                ),
                operation_name=f"DescribeInstanceTypes({instance_type})"
            )
            
            if not response.get('InstanceTypes'):
                logger.warning(f"No metadata found for instance type {instance_type}")
                return {}
            
            instance_info = response['InstanceTypes'][0]
            
            # Extract relevant metadata
            metadata = {
                'vcpu_count': instance_info.get('VCpuInfo', {}).get('DefaultVCpus'),
                'memory_mib': instance_info.get('MemoryInfo', {}).get('SizeInMiB'),
                'ebs_optimized': instance_info.get('EbsInfo', {}).get('EbsOptimizedSupport') == 'default',
                'network_performance': instance_info.get('NetworkInfo', {}).get('NetworkPerformance'),
                'instance_storage': instance_info.get('InstanceStorageInfo', {}).get('TotalSizeInGB', 0),
                'processor_info': instance_info.get('ProcessorInfo', {}).get('SupportedArchitectures', []),
                'hypervisor': instance_info.get('Hypervisor'),
                'current_generation': instance_info.get('CurrentGeneration', False)
            }
            
            # Cache the result
            await self.cache.set(cache_key, metadata, ttl=3600)
            
            logger.debug(f"Retrieved metadata for {instance_type} from AWS")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to get instance metadata for {instance_type}: {e}")
            return {}
    
    async def detect_implicit_resources(
        self,
        node: ERGNode,
        account_id: str
    ) -> List[ERGNode]:
        """Detect implicit resources for EC2 instance."""
        if node.resource_type != "aws_instance":
            return []
        
        implicit_resources = []
        
        # Detect implicit root EBS volume
        root_volume = self._create_implicit_root_volume(node, account_id)
        if root_volume:
            implicit_resources.append(root_volume)
        
        # Detect additional EBS volumes from block_device_mappings
        additional_volumes = await self._detect_additional_ebs_volumes(node, account_id)
        implicit_resources.extend(additional_volumes)
        
        # Detect implicit ENI
        eni = self._create_implicit_eni(node, account_id)
        if eni:
            implicit_resources.append(eni)
        
        # Detect public IP if present
        public_ip = self._detect_public_ip(node, account_id)
        if public_ip:
            implicit_resources.append(public_ip)
        
        logger.info(
            f"Detected {len(implicit_resources)} implicit resources for {node.terraform_address}"
        )
        
        return implicit_resources
    
    async def _detect_additional_ebs_volumes(
        self,
        parent: ERGNode,
        account_id: str
    ) -> List[ERGNode]:
        """Detect additional EBS volumes from block device mappings."""
        volumes = []
        
        # Check for ebs_block_device in attributes
        ebs_block_devices = parent.attributes.get('ebs_block_device', [])
        if not isinstance(ebs_block_devices, list):
            ebs_block_devices = [ebs_block_devices] if ebs_block_devices else []
        
        for idx, device in enumerate(ebs_block_devices):
            if not isinstance(device, dict):
                continue
            
            volume_id = hashlib.sha256(
                f"{parent.resource_id}:ebs_volume_{idx}".encode()
            ).hexdigest()[:16]
            
            volume = ERGNode(
                resource_id=volume_id,
                terraform_address=None,
                resource_type="aws_ebs_volume",
                provider="aws",
                region=parent.region,
                quantity=1,
                attributes={
                    'size': device.get('volume_size', 8),
                    'type': device.get('volume_type', 'gp3'),
                    'iops': device.get('iops'),
                    'throughput': device.get('throughput'),
                    'encrypted': device.get('encrypted', False),
                    'device_name': device.get('device_name')
                },
                enriched_attributes={},
                unknown_attributes=[],
                provenance=ResourceProvenance.IMPLICIT,
                parent_resource_id=parent.resource_id,
                confidence_level=ConfidenceLevel.HIGH,
                aws_account_id=account_id,
                dependencies=[parent.resource_id]
            )
            volumes.append(volume)
        
        return volumes
    
    def _detect_public_ip(
        self,
        parent: ERGNode,
        account_id: str
    ) -> ERGNode | None:
        """Detect public IP allocation."""
        # Check if instance has public IP
        associate_public_ip = parent.attributes.get('associate_public_ip_address_address', False)
        
        if not associate_public_ip:
            return None
        
        ip_id = hashlib.sha256(
            f"{parent.resource_id}:public_ip".encode()
        ).hexdigest()[:16]
        
        return ERGNode(
            resource_id=ip_id,
            terraform_address=None,
            resource_type="aws_eip",
            provider="aws",
            region=parent.region,
            quantity=1,
            attributes={
                'domain': 'vpc',
                'instance': parent.terraform_address
            },
            enriched_attributes={},
            unknown_attributes=[],
            provenance=ResourceProvenance.IMPLICIT,
            parent_resource_id=parent.resource_id,
            confidence_level=ConfidenceLevel.MEDIUM,
            aws_account_id=account_id,
            dependencies=[parent.resource_id]
        )
    
    def _create_implicit_root_volume(
        self,
        parent: ERGNode,
        account_id: str
    ) -> ERGNode | None:
        """Create implicit root EBS volume node."""
        # Check if root volume is explicitly declared
        root_block_device = parent.attributes.get('root_block_device')
        if root_block_device and isinstance(root_block_device, dict):
            # Explicitly configured, not implicit
            return None
        
        # Create implicit root volume
        volume_id = hashlib.sha256(
            f"{parent.resource_id}:root_volume".encode()
        ).hexdigest()[:16]
        
        return ERGNode(
            resource_id=volume_id,
            terraform_address=None,
            resource_type="aws_ebs_volume",
            provider="aws",
            region=parent.region,
            quantity=1,
            attributes={
                'size': 8,  # Default root volume size
                'type': 'gp3',  # Current default
                'encrypted': False
            },
            enriched_attributes={},
            unknown_attributes=[],
            provenance=ResourceProvenance.IMPLICIT,
            parent_resource_id=parent.resource_id,
            confidence_level=ConfidenceLevel.MEDIUM,
            aws_account_id=account_id,
            dependencies=[parent.resource_id]
        )
    
    def _create_implicit_eni(
        self,
        parent: ERGNode,
        account_id: str
    ) -> ERGNode | None:
        """Create implicit ENI node."""
        eni_id = hashlib.sha256(
            f"{parent.resource_id}:eni".encode()
        ).hexdigest()[:16]
        
        return ERGNode(
            resource_id=eni_id,
            terraform_address=None,
            resource_type="aws_network_interface",
            provider="aws",
            region=parent.region,
            quantity=1,
            attributes={
                'attachment': {
                    'instance': parent.terraform_address,
                    'device_index': 0
                }
            },
            enriched_attributes={},
            unknown_attributes=[],
            provenance=ResourceProvenance.IMPLICIT,
            parent_resource_id=parent.resource_id,
            confidence_level=ConfidenceLevel.HIGH,
            aws_account_id=account_id,
            dependencies=[parent.resource_id]
        )

