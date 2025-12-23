"""
Region aggregator for grouping costs by region.
"""
from typing import List, Dict
from decimal import Decimal
from collections import defaultdict
from app.schemas.cost import ResourceCost, AggregatedCost
from app.calculation.scenario_calculator import ScenarioCalculator
from app.analysis.diff_calculator import DiffCalculator
from app.calculation.confidence_calculator import ConfidenceCalculator
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RegionAggregator:
    """Aggregates costs by region."""
    
    def __init__(self, default_currency: str = "USD"):
        """
        Initialize region aggregator.
        
        Args:
            default_currency: Default currency
        """
        self.default_currency = default_currency
        self.scenario_calc = ScenarioCalculator(default_currency)
        self.diff_calc = DiffCalculator()
        self.confidence_calc = ConfidenceCalculator()
    
    def aggregate_by_region(self, resource_costs: List[ResourceCost]) -> List[AggregatedCost]:
        """
        Aggregate costs by region.
        
        Args:
            resource_costs: List of resource costs
            
        Returns:
            List of aggregated costs by region
        """
        # Group by region
        region_groups: Dict[str, List[ResourceCost]] = defaultdict(list)
        
        for resource_cost in resource_costs:
            region_groups[resource_cost.region].append(resource_cost)
        
        # Aggregate each region
        aggregated = []
        
        for region, costs in region_groups.items():
            aggregated_cost = self._aggregate_region(region, costs)
            aggregated.append(aggregated_cost)
        
        logger.info(f"Aggregated costs for {len(aggregated)} regions")
        
        return aggregated
    
    def _aggregate_region(self, region: str, costs: List[ResourceCost]) -> AggregatedCost:
        """
        Aggregate costs for a single region.
        
        Args:
            region: Region name
            costs: Resource costs for this region
            
        Returns:
            Aggregated cost
        """
        # Sum scenarios
        total_min = Decimal('0')
        total_expected = Decimal('0')
        total_max = Decimal('0')
        
        for cost in costs:
            total_min += cost.scenario.min
            total_expected += cost.scenario.expected
            total_max += cost.scenario.max
        
        # Create scenario
        scenario = self.scenario_calc.create_scenario(
            total_min,
            total_expected,
            total_max,
            self.default_currency
        )
        
        # Calculate diff
        diff = self.diff_calc.calculate_diff(scenario)
        
        # Aggregate confidence (lowest wins)
        confidences = [cost.confidence for cost in costs]
        confidence = self.confidence_calc.aggregate_confidence(confidences)
        
        return AggregatedCost(
            group_by="region",
            group_value=region,
            scenario=scenario,
            diff=diff,
            resource_count=len(costs),
            confidence=confidence
        )
