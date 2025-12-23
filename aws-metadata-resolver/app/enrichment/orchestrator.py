"""
Enrichment orchestrator - main coordinator for NRG → ERG conversion.
"""
import time
from typing import List, Dict, Any
from datetime import datetime
from app.schemas.erg import ERGNode, EnrichmentMetadata, ResourceProvenance
from app.schemas.api import NRGNode
from app.adapters.ec2 import EC2Adapter
from app.adapters.ebs import EBSAdapter
from app.adapters.elb import ELBAdapter
from app.adapters.rds import RDSAdapter
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EnrichmentOrchestrator:
    """Orchestrates enrichment of NRG to ERG."""
    
    def __init__(
        self,
        aws_client_manager,
        cache,
        retry_handler,
        enabled_adapters: List[str]
    ):
        """
        Initialize enrichment orchestrator.
        
        Args:
            aws_client_manager: AWS client manager
            cache: Cache implementation
            retry_handler: Retry handler
            enabled_adapters: List of enabled adapter names
        """
        self.aws_client_manager = aws_client_manager
        self.cache = cache
        self.retry_handler = retry_handler
        
        # Initialize service adapters
        self.adapters = self._initialize_adapters(enabled_adapters)
        
        # Metrics
        self.api_call_count = 0
    
    def _initialize_adapters(self, enabled_adapters: List[str]) -> List:
        """Initialize enabled service adapters."""
        adapters = []
        
        adapter_map = {
            'ec2': EC2Adapter,
            'ebs': EBSAdapter,
            'elb': ELBAdapter,
            'rds': RDSAdapter,
        }
        
        for adapter_name in enabled_adapters:
            if adapter_name in adapter_map:
                adapter_class = adapter_map[adapter_name]
                adapter = adapter_class(
                    self.aws_client_manager,
                    self.cache,
                    self.retry_handler
                )
                adapters.append(adapter)
                logger.info(f"Initialized {adapter_name} adapter")
        
        return adapters
    
    async def enrich(
        self,
        nrg_nodes: List[NRGNode],
        account_id: str = "unknown"
    ) -> tuple[List[ERGNode], EnrichmentMetadata]:
        """
        Enrich NRG to produce ERG.
        
        Args:
            nrg_nodes: List of NRG nodes from Plan Interpreter
            account_id: AWS account ID
            
        Returns:
            (ERG nodes, enrichment metadata)
        """
        start_time = time.time()
        
        logger.info(f"Starting enrichment of {len(nrg_nodes)} resources")
        
        # Convert NRG nodes to ERG nodes
        erg_nodes = self._convert_nrg_to_erg(nrg_nodes, account_id)
        
        # Enrich each node
        enriched_nodes = []
        failed_count = 0
        
        for node in erg_nodes:
            try:
                enriched_node = await self._enrich_node(node, account_id)
                enriched_nodes.append(enriched_node)
            except Exception as e:
                logger.error(f"Failed to enrich {node.terraform_address}: {e}")
                # Add node without enrichment
                enriched_nodes.append(node)
                failed_count += 1
        
        # Detect implicit resources
        implicit_nodes = await self._detect_all_implicit_resources(
            enriched_nodes,
            account_id
        )
        
        # Combine explicit and implicit nodes
        all_nodes = enriched_nodes + implicit_nodes
        
        # Build metadata
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Get cache hit rate
        cache_hit_rate = 0.0
        if hasattr(self.cache, 'hit_rate'):
            cache_hit_rate = self.cache.hit_rate
        
        metadata = EnrichmentMetadata(
            total_resources=len(all_nodes),
            terraform_resources=len(erg_nodes),
            implicit_resources=len(implicit_nodes),
            enriched_count=len(enriched_nodes) - failed_count,
            failed_count=failed_count,
            cache_hit_rate=cache_hit_rate,
            aws_api_calls=self.api_call_count,
            enrichment_duration_ms=duration_ms,
            enrichment_timestamp=datetime.utcnow()
        )
        
        logger.info(
            f"Enrichment complete: {len(all_nodes)} total resources "
            f"({len(implicit_nodes)} implicit) in {duration_ms}ms"
        )
        
        return all_nodes, metadata
    
    def _convert_nrg_to_erg(
        self,
        nrg_nodes: List[NRGNode],
        account_id: str
    ) -> List[ERGNode]:
        """Convert NRG nodes to ERG nodes."""
        erg_nodes = []
        
        for nrg_node in nrg_nodes:
            erg_node = ERGNode(
                resource_id=nrg_node.resource_id,
                terraform_address=nrg_node.terraform_address,
                resource_type=nrg_node.resource_type,
                provider=nrg_node.provider,
                region=nrg_node.region,
                quantity=nrg_node.quantity,
                module_path=nrg_node.module_path,
                dependencies=nrg_node.dependencies,
                attributes=nrg_node.attributes,
                unknown_attributes=nrg_node.unknown_attributes,
                enriched_attributes={},
                provenance=ResourceProvenance.TERRAFORM,
                parent_resource_id=None,
                confidence_level=nrg_node.confidence_level,
                aws_account_id=account_id
            )
            erg_nodes.append(erg_node)
        
        return erg_nodes
    
    async def _enrich_node(self, node: ERGNode, account_id: str) -> ERGNode:
        """Enrich a single node using appropriate adapter."""
        for adapter in self.adapters:
            if adapter.can_handle(node.resource_type):
                return await adapter.enrich(node, account_id)
        
        # No adapter found, return as-is
        logger.debug(f"No adapter for {node.resource_type}")
        return node
    
    async def _detect_all_implicit_resources(
        self,
        nodes: List[ERGNode],
        account_id: str
    ) -> List[ERGNode]:
        """Detect implicit resources for all nodes."""
        all_implicit = []
        
        for node in nodes:
            for adapter in self.adapters:
                if adapter.can_handle(node.resource_type):
                    implicit = await adapter.detect_implicit_resources(node, account_id)
                    all_implicit.extend(implicit)
        
        logger.info(f"Detected {len(all_implicit)} total implicit resources")
        
        return all_implicit
