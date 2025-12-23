"""
Confidence calculator for propagating confidence scores.
"""
from typing import List
from app.schemas.cost import ConfidenceLevel
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ConfidenceCalculator:
    """Calculates and propagates confidence scores."""
    
    @staticmethod
    def propagate_confidence(
        pricing_confidence: str,
        usage_confidence: str,
        metadata_confidence: str = "HIGH"
    ) -> ConfidenceLevel:
        """
        Propagate confidence from multiple sources.
        
        Rules:
        - ANY LOW → LOW
        - ANY MEDIUM (no LOW) → MEDIUM
        - ALL HIGH → HIGH
        
        Args:
            pricing_confidence: Confidence from pricing
            usage_confidence: Confidence from usage
            metadata_confidence: Confidence from metadata (default HIGH)
            
        Returns:
            Propagated confidence level
        """
        confidences = [
            ConfidenceLevel(pricing_confidence),
            ConfidenceLevel(usage_confidence),
            ConfidenceLevel(metadata_confidence)
        ]
        
        # LOW propagates
        if ConfidenceLevel.LOW in confidences:
            logger.debug("Confidence propagated to LOW (at least one LOW input)")
            return ConfidenceLevel.LOW
        
        # MEDIUM propagates if no LOW
        if ConfidenceLevel.MEDIUM in confidences:
            logger.debug("Confidence propagated to MEDIUM (at least one MEDIUM, no LOW)")
            return ConfidenceLevel.MEDIUM
        
        # All HIGH
        logger.debug("Confidence propagated to HIGH (all inputs HIGH)")
        return ConfidenceLevel.HIGH
    
    @staticmethod
    def aggregate_confidence(confidences: List[ConfidenceLevel]) -> ConfidenceLevel:
        """
        Aggregate confidence across multiple resources.
        
        Rule: Lowest confidence wins
        
        Args:
            confidences: List of confidence levels
            
        Returns:
            Aggregated confidence (lowest)
        """
        if not confidences:
            logger.warning("No confidences provided, defaulting to LOW")
            return ConfidenceLevel.LOW
        
        # LOW propagates
        if ConfidenceLevel.LOW in confidences:
            return ConfidenceLevel.LOW
        
        # MEDIUM propagates if no LOW
        if ConfidenceLevel.MEDIUM in confidences:
            return ConfidenceLevel.MEDIUM
        
        # All HIGH
        return ConfidenceLevel.HIGH
