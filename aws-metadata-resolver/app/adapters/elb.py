"""
ELB service adapter (ALB/NLB) - AUTHORITATIVE via AWS APIs.
"""
from typing import List, Dict, Any
from app.adapters.base import BaseServiceAdapter
from app.schemas.erg import ERGNode, ResourceProvenance, ConfidenceLevel
from app.cache.interface import generate_cache_key
from app.utils.logger import get_logger
import hashlib

logger = get_logger(__name__)


class ELBAdapter(BaseServiceAdapter):
    """ELB service adapter for ALB/NLB enrichment using real AWS APIs."""
    
    def _get_service_name(self) -> str:
        return "elb"
    
    def can_handle(self, resource_type: str) -> bool:
        """Handle both aws_lb and aws_alb resource types."""
        return resource_type in ['aws_lb', 'aws_alb', 'aws_elb']
    
    async def enrich(self, node: ERGNode, account_id: str) -> ERGNode:
        """Enrich load balancer with AWS metadata from DescribeLoadBalancers."""
        if not self.can_handle(node.resource_type):
            return node
        
        logger.info(f"Enriching load balancer: {node.terraform_address}")
        
        # Get LB name from Terraform attributes
        lb_name = node.attributes.get('name')
        if not lb_name:
            logger.warning(f"No load balancer name found for {node.terraform_address}")
            node.confidence_level = ConfidenceLevel.LOW
            return node
        
        # Get LB metadata from AWS
        lb_metadata = await self._get_lb_from_aws(
            lb_name,
            node.region or 'us-east-1',
            account_id
        )
        
        if lb_metadata:
            node.enriched_attributes.update(lb_metadata)
            logger.info(f"Enriched load balancer with {len(lb_metadata)} attributes from AWS")
        else:
            logger.warning(f"Could not retrieve AWS metadata for {node.terraform_address}")
            node.confidence_level = ConfidenceLevel.LOW
        
        return node
    
    async def _get_lb_from_aws(
        self,
        lb_name: str,
        region: str,
        account_id: str
    ) -> Dict[str, Any]:
        """
        Get load balancer metadata from AWS DescribeLoadBalancers API.
        
        Args:
            lb_name: Load balancer name
            region: AWS region
            account_id: AWS account ID
            
        Returns:
            Dict of LB metadata from AWS
        """
        # Check cache first
        cache_key = generate_cache_key(
            account_id,
            region,
            'elbv2',
            'load_balancer',
            lb_name
        )
        
        cached = await self.cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for load balancer {lb_name}")
            return cached
        
        # Call AWS API (boto3 is synchronous)
        try:
            elbv2_client = self.aws_client_manager.get_client('elbv2', region)
            
            # Use retry handler (synchronous)
            response = self.retry_handler.execute_with_retry(
                lambda: elbv2_client.describe_load_balancers(Names=[lb_name]),
                operation_name=f"DescribeLoadBalancers({lb_name})"
            )
            
            if not response.get('LoadBalancers'):
                logger.warning(f"No load balancer found: {lb_name}")
                return {}
            
            lb_info = response['LoadBalancers'][0]
            
            # Get load balancer attributes
            lb_arn = lb_info.get('LoadBalancerArn')
            attributes = await self._get_lb_attributes(lb_arn, region, account_id)
            
            # Extract metadata from AWS response
            metadata = {
                'load_balancer_arn': lb_arn,
                'load_balancer_type': lb_info.get('Type'),  # 'application' or 'network'
                'scheme': lb_info.get('Scheme'),  # 'internet-facing' or 'internal'
                'vpc_id': lb_info.get('VpcId'),
                'availability_zones': [az['ZoneName'] for az in lb_info.get('AvailabilityZones', [])],
                'dns_name': lb_info.get('DNSName'),
                'canonical_hosted_zone_id': lb_info.get('CanonicalHostedZoneId'),
                'state': lb_info.get('State', {}).get('Code'),
                'ip_address_type': lb_info.get('IpAddressType'),
            }
            
            # Add attributes from DescribeLoadBalancerAttributes
            if attributes:
                metadata.update(attributes)
            
            # Cache the result
            await self.cache.set(cache_key, metadata, ttl=3600)
            
            logger.debug(f"Retrieved metadata for {lb_name} from AWS")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to get load balancer metadata for {lb_name}: {e}")
            return {}
    
    async def _get_lb_attributes(
        self,
        lb_arn: str,
        region: str,
        account_id: str
    ) -> Dict[str, Any]:
        """Get load balancer attributes from AWS."""
        try:
            elbv2_client = self.aws_client_manager.get_client('elbv2', region)
            
            # boto3 is synchronous
            response = self.retry_handler.execute_with_retry(
                lambda: elbv2_client.describe_load_balancer_attributes(
                    LoadBalancerArn=lb_arn
                ),
                operation_name="DescribeLoadBalancerAttributes"
            )
            
            # Convert attributes list to dict
            attrs = {}
            for attr in response.get('Attributes', []):
                key = attr.get('Key', '').replace('.', '_')
                value = attr.get('Value')
                
                # Convert boolean strings
                if value in ['true', 'false']:
                    value = (value == 'true')
                
                attrs[key] = value
            
            return attrs
            
        except Exception as e:
            logger.error(f"Failed to get LB attributes: {e}")
            return {}
    
    async def detect_implicit_resources(
        self,
        node: ERGNode,
        account_id: str
    ) -> List[ERGNode]:
        """Detect implicit resources for load balancer using AWS APIs."""
        if not self.can_handle(node.resource_type):
            return []
        
        implicit_resources = []
        
        # Get LB ARN from enriched attributes
        lb_arn = node.enriched_attributes.get('load_balancer_arn')
        if not lb_arn:
            logger.warning(f"No LB ARN found for {node.terraform_address}, cannot detect listeners")
            return []
        
        # Detect actual listeners from AWS
        listeners = await self._detect_listeners_from_aws(
            lb_arn,
            node,
            account_id
        )
        implicit_resources.extend(listeners)
        
        # Create LCU tracker as first-class resource
        lcu = self._create_lcu_tracker(node, account_id)
        if lcu:
            implicit_resources.append(lcu)
        
        logger.info(
            f"Detected {len(implicit_resources)} implicit resources for {node.terraform_address}"
        )
        
        return implicit_resources
    
    async def _detect_listeners_from_aws(
        self,
        lb_arn: str,
        parent: ERGNode,
        account_id: str
    ) -> List[ERGNode]:
        """Detect actual listeners from AWS DescribeListeners API."""
        # Check cache
        cache_key = generate_cache_key(
            account_id,
            parent.region or 'us-east-1',
            'elbv2',
            'listeners',
            lb_arn
        )
        
        cached = await self.cache.get(cache_key)
        if cached:
            return self._build_listener_nodes(cached, parent, account_id)
        
        try:
            elbv2_client = self.aws_client_manager.get_client('elbv2', parent.region or 'us-east-1')
            
            # boto3 is synchronous
            response = self.retry_handler.execute_with_retry(
                lambda: elbv2_client.describe_listeners(LoadBalancerArn=lb_arn),
                operation_name="DescribeListeners"
            )
            
            listeners_data = response.get('Listeners', [])
            
            # Cache the result
            await self.cache.set(cache_key, listeners_data, ttl=3600)
            
            return self._build_listener_nodes(listeners_data, parent, account_id)
            
        except Exception as e:
            logger.error(f"Failed to get listeners for {lb_arn}: {e}")
            return []
    
    def _build_listener_nodes(
        self,
        listeners_data: List[Dict],
        parent: ERGNode,
        account_id: str
    ) -> List[ERGNode]:
        """Build ERG nodes from AWS listener data."""
        nodes = []
        
        for idx, listener in enumerate(listeners_data):
            listener_arn = listener.get('ListenerArn', '')
            listener_id = hashlib.sha256(
                f"{parent.resource_id}:listener:{listener_arn}".encode()
            ).hexdigest()[:16]
            
            node = ERGNode(
                resource_id=listener_id,
                terraform_address=None,
                resource_type="aws_lb_listener",
                provider="aws",
                region=parent.region,
                quantity=1,
                attributes={
                    'listener_arn': listener_arn,
                    'port': listener.get('Port'),
                    'protocol': listener.get('Protocol'),
                    'ssl_policy': listener.get('SslPolicy'),
                    'certificates': listener.get('Certificates', []),
                    'default_actions': listener.get('DefaultActions', [])
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
        
        logger.info(f"Built {len(nodes)} listener nodes from AWS data")
        return nodes
    
    def _create_lcu_tracker(
        self,
        parent: ERGNode,
        account_id: str
    ) -> ERGNode | None:
        """Create LCU (Load Balancer Capacity Units) tracker as first-class resource."""
        lb_type = parent.enriched_attributes.get('load_balancer_type')
        
        # LCUs only apply to ALB and NLB
        if lb_type not in ['application', 'network']:
            return None
        
        lcu_id = hashlib.sha256(
            f"{parent.resource_id}:lcu".encode()
        ).hexdigest()[:16]
        
        # LCU dimensions vary by type
        lcu_dimensions = {
            'application': ['new_connections', 'active_connections', 'processed_bytes', 'rule_evaluations'],
            'network': ['new_connections', 'active_connections', 'processed_bytes', 'tcp_connections']
        }
        
        return ERGNode(
            resource_id=lcu_id,
            terraform_address=None,
            resource_type="aws_lb_capacity_units",
            provider="aws",
            region=parent.region,
            quantity=1,
            attributes={
                'load_balancer_type': lb_type,
                'load_balancer_arn': parent.enriched_attributes.get('load_balancer_arn'),
                'lcu_dimensions': lcu_dimensions.get(lb_type, []),
                'billing_model': 'per_lcu_hour'
            },
            enriched_attributes={},
            unknown_attributes=[],
            provenance=ResourceProvenance.IMPLICIT,
            parent_resource_id=parent.resource_id,
            confidence_level=ConfidenceLevel.HIGH,
            aws_account_id=account_id,
            dependencies=[parent.resource_id]
        )


