"""
SKU matching engine for pricing lookups.
"""
from typing import List, Dict, Any, Optional
from app.schemas.pricing import NormalizedPrice, ConfidenceLevel
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SKUMatcher:
    """Matches resource attributes to pricing SKUs."""
    
    @staticmethod
    def match_prices(
        normalized_prices: List[NormalizedPrice],
        resource_type: str,
        attributes: Dict[str, Any],
        usage_type: Optional[str] = None
    ) -> tuple[List[NormalizedPrice], ConfidenceLevel]:
        """
        Match normalized prices to resource attributes.
        
        Args:
            normalized_prices: List of normalized prices from AWS
            resource_type: Resource type to match
            attributes: Resource attributes for matching
            usage_type: Optional usage type for stricter matching
            
        Returns:
            Tuple of (matched prices, confidence level)
        """
        if not normalized_prices:
            logger.warning("No normalized prices provided for matching")
            return [], ConfidenceLevel.LOW
        
        # Filter by resource type
        type_matches = [
            p for p in normalized_prices
            if p.resource_type == resource_type
        ]
        
        if not type_matches:
            logger.warning(f"No prices found for resource_type: {resource_type}")
            return [], ConfidenceLevel.LOW
        
        # If no attributes provided, return all type matches with low confidence
        if not attributes:
            logger.info(f"No attributes provided, returning {len(type_matches)} type matches")
            return type_matches, ConfidenceLevel.LOW
        
        # Match by attributes
        exact_matches = []
        partial_matches = []
        
        for price in type_matches:
            match_score = SKUMatcher._calculate_match_score(price.attributes, attributes)
            
            if match_score == 1.0:
                exact_matches.append(price)
            elif match_score > 0.5:
                partial_matches.append(price)
        
        # Determine best matches and confidence
        if exact_matches:
            if len(exact_matches) == 1:
                # HIGH confidence requires usage_type and unit compatibility
                price = exact_matches[0]
                has_usage_type = bool(price.usage_type)
                has_unit = bool(price.unit)
                
                if has_usage_type and has_unit:
                    logger.info("Found single exact match with usage_type and unit - HIGH confidence")
                    return exact_matches, ConfidenceLevel.HIGH
                else:
                    logger.info("Found single exact match but missing usage_type or unit - MEDIUM confidence")
                    return exact_matches, ConfidenceLevel.MEDIUM
            else:
                logger.info(f"Found {len(exact_matches)} exact matches - MEDIUM confidence")
                return exact_matches, ConfidenceLevel.MEDIUM
        
        if partial_matches:
            logger.info(f"Found {len(partial_matches)} partial matches - MEDIUM confidence")
            return partial_matches, ConfidenceLevel.MEDIUM
        
        # Fallback to type matches
        logger.warning("No attribute matches, falling back to type matches - LOW confidence")
        return type_matches, ConfidenceLevel.LOW
    
    @staticmethod
    def _calculate_match_score(price_attrs: Dict[str, Any], request_attrs: Dict[str, Any]) -> float:
        """
        Calculate match score between price attributes and request attributes.
        
        Args:
            price_attrs: Attributes from pricing SKU
            request_attrs: Attributes from request
            
        Returns:
            Match score (0.0 to 1.0)
        """
        if not request_attrs:
            return 0.0
        
        matched = 0
        total = len(request_attrs)
        
        for key, value in request_attrs.items():
            price_value = price_attrs.get(key)
            
            if price_value is None:
                continue
            
            # Normalize values for comparison
            price_value_str = str(price_value).lower().strip()
            request_value_str = str(value).lower().strip()
            
            if price_value_str == request_value_str:
                matched += 1
        
        return matched / total if total > 0 else 0.0
    
    @staticmethod
    def filter_by_usage_type(
        prices: List[NormalizedPrice],
        usage_type: Optional[str] = None
    ) -> List[NormalizedPrice]:
        """
        Filter prices by usage type.
        
        Args:
            prices: List of prices
            usage_type: Usage type to filter by (optional)
            
        Returns:
            Filtered prices
        """
        if not usage_type:
            return prices
        
        filtered = [p for p in prices if usage_type.lower() in p.usage_type.lower()]
        
        if not filtered:
            logger.warning(f"No prices found for usage_type: {usage_type}")
            return prices
        
        return filtered
