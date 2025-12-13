"""Confidence calculation for resources."""

from typing import Dict, Any, List

from .extractors import AttributeExtractor


class ConfidenceCalculator:
    """Calculates confidence scores for resources."""
    
    @staticmethod
    def calculate(
        resource_type: str,
        attributes: Dict[str, Any],
        computed_attributes: List[str]
    ) -> float:
        """Calculate confidence score for a resource.
        
        Confidence is based on:
        - Percentage of known attributes (70% weight)
        - Percentage of critical attributes known (30% weight)
        
        Args:
            resource_type: Resource type
            attributes: Resource attributes
            computed_attributes: List of computed attributes
            
        Returns:
            Confidence score (0.0-1.0)
        """
        # Count total attributes
        total_attrs = AttributeExtractor.count_attributes(attributes)
        if total_attrs == 0:
            return 0.0
        
        # Count computed attributes
        computed_count = len(computed_attributes)
        known_count = max(0, total_attrs - computed_count)
        
        # Base confidence: known / total
        base_confidence = known_count / total_attrs if total_attrs > 0 else 0.0
        
        # Critical attributes confidence
        critical_attrs = AttributeExtractor.get_critical_attributes(resource_type)
        if not critical_attrs:
            # No critical attributes defined, use base confidence only
            return base_confidence
        
        # Check how many critical attributes are known
        critical_known = 0
        for attr in critical_attrs:
            # Check if attribute exists and is not computed
            if attr in attributes and attr not in computed_attributes:
                critical_known += 1
        
        critical_confidence = critical_known / len(critical_attrs)
        
        # Weighted average: 70% base + 30% critical
        final_confidence = 0.7 * base_confidence + 0.3 * critical_confidence
        
        # Clamp to [0.0, 1.0]
        return max(0.0, min(1.0, final_confidence))
    
    @staticmethod
    def get_confidence_level(confidence: float) -> str:
        """Get confidence level description.
        
        Args:
            confidence: Confidence score
            
        Returns:
            Confidence level (HIGH, MEDIUM, LOW)
        """
        if confidence >= 0.8:
            return "HIGH"
        elif confidence >= 0.5:
            return "MEDIUM"
        else:
            return "LOW"
