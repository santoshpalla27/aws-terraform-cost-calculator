"""
EBS service adapter - NO HARDCODED DEFAULTS.
"""
from typing import List
from app.adapters.base import BaseServiceAdapter
from app.schemas.erg import ERGNode, ConfidenceLevel
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EBSAdapter(BaseServiceAdapter):
    """EBS service adapter for enrichment - authoritative only."""
    
    def _get_service_name(self) -> str:
        return "ebs"
    
    async def enrich(self, node: ERGNode, account_id: str) -> ERGNode:
        """Enrich EBS volume - NO DEFAULTS, only AWS data."""
        if node.resource_type != "aws_ebs_volume":
            return node
        
        logger.info(f"Enriching EBS volume: {node.terraform_address}")
        
        # Mark unknown attributes explicitly
        unknown_attrs = []
        
        if 'type' not in node.attributes:
            unknown_attrs.append('type')
            logger.warning(f"Volume type unknown for {node.terraform_address}")
        
        if 'iops' not in node.attributes:
            unknown_attrs.append('iops')
        
        if 'throughput' not in node.attributes:
            unknown_attrs.append('throughput')
        
        if 'encrypted' not in node.attributes:
            unknown_attrs.append('encrypted')
        
        # Update unknown attributes list
        node.unknown_attributes.extend(unknown_attrs)
        
        # Lower confidence if critical attributes are unknown
        if 'type' in unknown_attrs:
            node.confidence_level = ConfidenceLevel.LOW
        
        logger.info(f"EBS volume enrichment complete: {len(unknown_attrs)} unknown attributes")
        
        return node
    
    async def detect_implicit_resources(
        self,
        node: ERGNode,
        account_id: str
    ) -> List[ERGNode]:
        """EBS volumes don't create implicit resources."""
        return []

