"""
Pricing service orchestrator.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.schemas.pricing import (
    NormalizedPrice,
    PricingMetadata,
    PriceLookupRequest,
    PriceLookupResponse,
    ConfidenceLevel
)
from app.pricing.aws_pricing_client import AWSPricingClient
from app.pricing.sku_matcher import SKUMatcher
from app.cache.interface import CacheInterface
from app.utils.logger import get_logger
from app.utils.region_mapper import RegionMapper
import hashlib
import json

logger = get_logger(__name__)


class PricingService:
    """Orchestrates pricing lookups."""
    
    def __init__(self, pricing_client: AWSPricingClient, cache: CacheInterface):
        """
        Initialize pricing service.
        
        Args:
            pricing_client: AWS Pricing API client
            cache: Cache interface
        """
        self.pricing_client = pricing_client
        self.cache = cache
        self.normalizers = self._initialize_normalizers()
    
    def _initialize_normalizers(self) -> Dict[str, Any]:
        """Initialize service normalizers."""
        from app.pricing.normalizers.ec2 import EC2PricingNormalizer
        from app.pricing.normalizers.ebs import EBSPricingNormalizer
        from app.pricing.normalizers.elb import ELBPricingNormalizer
        from app.pricing.normalizers.rds import RDSPricingNormalizer
        
        normalizers = {}
        
        # Register normalizers
        for normalizer_class in [EC2PricingNormalizer, EBSPricingNormalizer, ELBPricingNormalizer, RDSPricingNormalizer]:
            normalizer = normalizer_class()
            normalizers[normalizer.get_service_name()] = normalizer
        
        logger.info(f"Initialized {len(normalizers)} pricing normalizers: {list(normalizers.keys())}")
        
        return normalizers
    
    async def lookup_pricing(self, request: PriceLookupRequest) -> PriceLookupResponse:
        """
        Lookup pricing for a resource.
        
        Args:
            request: Pricing lookup request
            
        Returns:
            Pricing lookup response
        """
        logger.info(f"Pricing lookup: service={request.service}, region={request.region}, resource_type={request.resource_type}")
        
        # Validate region
        if not RegionMapper.is_supported_region(request.region):
            logger.error(f"Unsupported region: {request.region}")
            return PriceLookupResponse(
                prices=[],
                confidence_level=ConfidenceLevel.LOW,
                metadata=None
            )
        
        # Generate cache key
        cache_key = self._generate_cache_key(request)
        
        # Check cache
        cached_response = await self.cache.get(cache_key)
        if cached_response:
            logger.info(f"Cache hit for {cache_key}")
            return PriceLookupResponse(**cached_response)
        
        logger.info(f"Cache miss for {cache_key}")
        
        # Get normalizer
        normalizer = self.normalizers.get(request.service)
        if not normalizer:
            logger.error(f"No normalizer for service: {request.service}")
            return PriceLookupResponse(
                prices=[],
                confidence_level=ConfidenceLevel.LOW,
                metadata=None
            )
        
        # Fetch pricing data
        try:
            pricing_data = await self.pricing_client.fetch_service_pricing(request.service)
        except Exception as e:
            logger.error(f"Failed to fetch pricing data: {e}")
            return PriceLookupResponse(
                prices=[],
                confidence_level=ConfidenceLevel.LOW,
                metadata=None
            )
        
        # Normalize pricing
        normalized_prices = normalizer.normalize(pricing_data, request.region)
        
        # Match SKUs
        matched_prices, confidence = SKUMatcher.match_prices(
            normalized_prices,
            request.resource_type,
            request.attributes
        )
        
        # Build metadata
        metadata = PricingMetadata(
            service=request.service,
            version=pricing_data.get('version', 'unknown'),
            publication_date=datetime.fromisoformat(pricing_data.get('publicationDate', datetime.utcnow().isoformat()).replace('Z', '+00:00')),
            last_updated=datetime.utcnow(),
            source="AWS Price List API",
            total_skus=len(pricing_data.get('products', {}))
        )
        
        # Build response
        response = PriceLookupResponse(
            prices=matched_prices,
            confidence_level=confidence,
            metadata=metadata
        )
        
        # Cache response
        await self.cache.set(cache_key, response.model_dump(), ttl=86400)
        
        logger.info(f"Returning {len(matched_prices)} prices with confidence {confidence}")
        
        return response
    
    def _generate_cache_key(self, request: PriceLookupRequest) -> str:
        """
        Generate deterministic cache key.
        
        Args:
            request: Pricing lookup request
            
        Returns:
            Cache key
        """
        # Sort attributes for deterministic key
        attrs_str = json.dumps(request.attributes, sort_keys=True)
        attrs_hash = hashlib.sha256(attrs_str.encode()).hexdigest()[:16]
        
        return f"pricing:{request.service}:{request.region}:{request.resource_type}:{attrs_hash}"
