"""
RDS service adapter - AUTHORITATIVE via AWS APIs.
"""
from typing import List, Dict, Any
from app.adapters.base import BaseServiceAdapter
from app.schemas.erg import ERGNode, ResourceProvenance, ConfidenceLevel
from app.cache.interface import generate_cache_key
from app.utils.logger import get_logger
import hashlib

logger = get_logger(__name__)


class RDSAdapter(BaseServiceAdapter):
    """RDS service adapter for enrichment using real AWS APIs."""
    
    def _get_service_name(self) -> str:
        return "rds"
    
    def can_handle(self, resource_type: str) -> bool:
        """Handle RDS resource types."""
        return resource_type in ['aws_db_instance', 'aws_db_cluster', 'aws_rds_cluster']
    
    async def enrich(self, node: ERGNode, account_id: str) -> ERGNode:
        """Enrich RDS instance with AWS metadata from DescribeDBInstances."""
        if not self.can_handle(node.resource_type):
            return node
        
        logger.info(f"Enriching RDS instance: {node.terraform_address}")
        
        # Get DB identifier from Terraform attributes
        db_identifier = node.attributes.get('identifier')
        if not db_identifier:
            logger.warning(f"No DB identifier found for {node.terraform_address}")
            node.confidence_level = ConfidenceLevel.LOW
            return node
        
        # Get RDS metadata from AWS
        rds_metadata = await self._get_db_instance_from_aws(
            db_identifier,
            node.region or 'us-east-1',
            account_id
        )
        
        if rds_metadata:
            node.enriched_attributes.update(rds_metadata)
            logger.info(f"Enriched RDS instance with {len(rds_metadata)} attributes from AWS")
        else:
            logger.warning(f"Could not retrieve AWS metadata for {node.terraform_address}")
            node.confidence_level = ConfidenceLevel.LOW
        
        return node
    
    async def _get_db_instance_from_aws(
        self,
        db_identifier: str,
        region: str,
        account_id: str
    ) -> Dict[str, Any]:
        """
        Get DB instance metadata from AWS DescribeDBInstances API.
        
        Args:
            db_identifier: DB instance identifier
            region: AWS region
            account_id: AWS account ID
            
        Returns:
            Dict of DB instance metadata from AWS
        """
        # Check cache first
        cache_key = generate_cache_key(
            account_id,
            region,
            'rds',
            'db_instance',
            db_identifier
        )
        
        cached = await self.cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for DB instance {db_identifier}")
            return cached
        
        # Call AWS API
        try:
            rds_client = self.aws_client_manager.get_client('rds', region)
            
            # boto3 is synchronous
            response = self.retry_handler.execute_with_retry(
                lambda: rds_client.describe_db_instances(
                    DBInstanceIdentifier=db_identifier
                ),
                operation_name=f"DescribeDBInstances({db_identifier})"
            )
            
            if not response.get('DBInstances'):
                logger.warning(f"No DB instance found: {db_identifier}")
                return {}
            
            db_info = response['DBInstances'][0]
            
            # Extract metadata from AWS response
            metadata = {
                'db_instance_arn': db_info.get('DBInstanceArn'),
                'db_instance_class': db_info.get('DBInstanceClass'),
                'engine': db_info.get('Engine'),
                'engine_version': db_info.get('EngineVersion'),
                'allocated_storage_gb': db_info.get('AllocatedStorage'),
                'storage_type': db_info.get('StorageType'),
                'iops': db_info.get('Iops'),
                'storage_throughput': db_info.get('StorageThroughput'),
                'storage_encrypted': db_info.get('StorageEncrypted', False),
                'multi_az': db_info.get('MultiAZ', False),
                'backup_retention_period': db_info.get('BackupRetentionPeriod', 0),
                'preferred_backup_window': db_info.get('PreferredBackupWindow'),
                'availability_zone': db_info.get('AvailabilityZone'),
                'vpc_id': db_info.get('DBSubnetGroup', {}).get('VpcId'),
                'publicly_accessible': db_info.get('PubliclyAccessible', False),
                'db_instance_status': db_info.get('DBInstanceStatus'),
                'license_model': db_info.get('LicenseModel'),
                'performance_insights_enabled': db_info.get('PerformanceInsightsEnabled', False)
            }
            
            # Cache the result
            await self.cache.set(cache_key, metadata, ttl=3600)
            
            logger.debug(f"Retrieved metadata for {db_identifier} from AWS")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to get DB instance metadata for {db_identifier}: {e}")
            return {}
    
    async def detect_implicit_resources(
        self,
        node: ERGNode,
        account_id: str
    ) -> List[ERGNode]:
        """Detect implicit resources for RDS using AWS metadata."""
        if not self.can_handle(node.resource_type):
            return []
        
        implicit_resources = []
        
        # Use AWS-enriched metadata instead of Terraform attributes
        allocated_storage = node.enriched_attributes.get('allocated_storage_gb')
        backup_retention = node.enriched_attributes.get('backup_retention_period', 0)
        multi_az = node.enriched_attributes.get('multi_az', False)
        
        # Detect RDS storage (always present)
        if allocated_storage:
            storage = self._create_implicit_storage(node, account_id, allocated_storage)
            if storage:
                implicit_resources.append(storage)
        
        # Detect backup storage (only if retention > 0)
        if backup_retention > 0:
            backup = self._create_implicit_backup_storage(node, account_id, backup_retention)
            if backup:
                implicit_resources.append(backup)
        
        # Detect multi-AZ replica (only if multi_az is true)
        if multi_az:
            replica = self._create_multi_az_replica(node, account_id)
            if replica:
                implicit_resources.append(replica)
        
        # Detect snapshots from AWS
        snapshots = await self._detect_snapshots_from_aws(node, account_id)
        implicit_resources.extend(snapshots)
        
        logger.info(
            f"Detected {len(implicit_resources)} implicit resources for {node.terraform_address}"
        )
        
        return implicit_resources
    
    def _create_implicit_storage(
        self,
        parent: ERGNode,
        account_id: str,
        allocated_storage: int
    ) -> ERGNode | None:
        """Create implicit RDS storage node from AWS data."""
        storage_id = hashlib.sha256(
            f"{parent.resource_id}:storage".encode()
        ).hexdigest()[:16]
        
        return ERGNode(
            resource_id=storage_id,
            terraform_address=None,
            resource_type="aws_rds_storage",
            provider="aws",
            region=parent.region,
            quantity=1,
            attributes={
                'allocated_storage_gb': allocated_storage,
                'storage_type': parent.enriched_attributes.get('storage_type'),
                'iops': parent.enriched_attributes.get('iops'),
                'storage_throughput': parent.enriched_attributes.get('storage_throughput'),
                'storage_encrypted': parent.enriched_attributes.get('storage_encrypted', False)
            },
            enriched_attributes={},
            unknown_attributes=[],
            provenance=ResourceProvenance.IMPLICIT,
            parent_resource_id=parent.resource_id,
            confidence_level=ConfidenceLevel.HIGH,
            aws_account_id=account_id,
            dependencies=[parent.resource_id]
        )
    
    def _create_implicit_backup_storage(
        self,
        parent: ERGNode,
        account_id: str,
        retention_period: int
    ) -> ERGNode | None:
        """Create implicit RDS backup storage node from AWS data."""
        backup_id = hashlib.sha256(
            f"{parent.resource_id}:backup".encode()
        ).hexdigest()[:16]
        
        return ERGNode(
            resource_id=backup_id,
            terraform_address=None,
            resource_type="aws_rds_backup_storage",
            provider="aws",
            region=parent.region,
            quantity=1,
            attributes={
                'retention_period_days': retention_period,
                'backup_window': parent.enriched_attributes.get('preferred_backup_window')
            },
            enriched_attributes={},
            unknown_attributes=[],
            provenance=ResourceProvenance.IMPLICIT,
            parent_resource_id=parent.resource_id,
            confidence_level=ConfidenceLevel.HIGH,
            aws_account_id=account_id,
            dependencies=[parent.resource_id]
        )
    
    def _create_multi_az_replica(
        self,
        parent: ERGNode,
        account_id: str
    ) -> ERGNode | None:
        """Create multi-AZ replica node from AWS data."""
        replica_id = hashlib.sha256(
            f"{parent.resource_id}:multi_az_replica".encode()
        ).hexdigest()[:16]
        
        return ERGNode(
            resource_id=replica_id,
            terraform_address=None,
            resource_type="aws_rds_replica",
            provider="aws",
            region=parent.region,
            quantity=1,
            attributes={
                'replica_type': 'multi_az',
                'instance_class': parent.enriched_attributes.get('db_instance_class')
            },
            enriched_attributes={},
            unknown_attributes=[],
            provenance=ResourceProvenance.IMPLICIT,
            parent_resource_id=parent.resource_id,
            confidence_level=ConfidenceLevel.HIGH,
            aws_account_id=account_id,
            dependencies=[parent.resource_id]
        )
    
    async def _detect_snapshots_from_aws(
        self,
        parent: ERGNode,
        account_id: str
    ) -> List[ERGNode]:
        """Detect DB snapshots from AWS DescribeDBSnapshots API."""
        db_identifier = parent.attributes.get('identifier')
        if not db_identifier:
            return []
        
        # Check cache
        cache_key = generate_cache_key(
            account_id,
            parent.region or 'us-east-1',
            'rds',
            'snapshots',
            db_identifier
        )
        
        cached = await self.cache.get(cache_key)
        if cached:
            return self._build_snapshot_nodes(cached, parent, account_id)
        
        try:
            rds_client = self.aws_client_manager.get_client('rds', parent.region or 'us-east-1')
            
            # boto3 is synchronous
            response = self.retry_handler.execute_with_retry(
                lambda: rds_client.describe_db_snapshots(
                    DBInstanceIdentifier=db_identifier
                ),
                operation_name="DescribeDBSnapshots"
            )
            
            snapshots_data = response.get('DBSnapshots', [])
            
            # Cache the result
            await self.cache.set(cache_key, snapshots_data, ttl=3600)
            
            return self._build_snapshot_nodes(snapshots_data, parent, account_id)
            
        except Exception as e:
            logger.error(f"Failed to get snapshots for {db_identifier}: {e}")
            return []
    
    def _build_snapshot_nodes(
        self,
        snapshots_data: List[Dict],
        parent: ERGNode,
        account_id: str
    ) -> List[ERGNode]:
        """Build ERG nodes from AWS snapshot data."""
        nodes = []
        
        for snapshot in snapshots_data:
            snapshot_id = snapshot.get('DBSnapshotIdentifier', '')
            node_id = hashlib.sha256(
                f"{parent.resource_id}:snapshot:{snapshot_id}".encode()
            ).hexdigest()[:16]
            
            node = ERGNode(
                resource_id=node_id,
                terraform_address=None,
                resource_type="aws_db_snapshot",
                provider="aws",
                region=parent.region,
                quantity=1,
                attributes={
                    'snapshot_id': snapshot_id,
                    'snapshot_type': snapshot.get('SnapshotType'),
                    'allocated_storage_gb': snapshot.get('AllocatedStorage'),
                    'encrypted': snapshot.get('Encrypted', False),
                    'snapshot_create_time': str(snapshot.get('SnapshotCreateTime', ''))
                },
                enriched_attributes={},
                unknown_attributes=[],
                provenance=ResourceProvenance.IMPLICIT,
                parent_resource_id=parent.resource_id,
                confidence_level=ConfidenceLevel.HIGH,
                aws_account_id=account_id,
                dependencies=[parent.resource_id]
            )
            nodes.append(node)
        
        logger.info(f"Built {len(nodes)} snapshot nodes from AWS data")
        return nodes

