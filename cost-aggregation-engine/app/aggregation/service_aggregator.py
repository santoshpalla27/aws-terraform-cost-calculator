"""
Service aggregator for grouping costs by service.
"""
from typing import List, Dict
from decimal import Decimal
from collections import defaultdict
from app.schemas.cost import ResourceCost, AggregatedCost, CostScenario, ConfidenceLevel
from app.calculation.scenario_calculator import ScenarioCalculator
from app.analysis.diff_calculator import DiffCalculator
from app.calculation.confidence_calculator import ConfidenceCalculator
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ServiceAggregator:
    """Aggregates costs by service."""
    
    def __init__(self, default_currency: str = "USD"):
        """
        Initialize service aggregator.
        
        Args:
            default_currency: Default currency
        """
        self.default_currency = default_currency
        self.scenario_calc = ScenarioCalculator(default_currency)
        self.diff_calc = DiffCalculator()
        self.confidence_calc = ConfidenceCalculator()
    
    def aggregate_by_service(self, resource_costs: List[ResourceCost]) -> List[AggregatedCost]:
        """
        Aggregate costs by service.
        
        Args:
            resource_costs: List of resource costs
            
        Returns:
            List of aggregated costs by service
        """
        # Group by service
        service_groups: Dict[str, List[ResourceCost]] = defaultdict(list)
        
        for resource_cost in resource_costs:
            service_groups[resource_cost.service].append(resource_cost)
        
        # Aggregate each service
        aggregated = []
        
        for service, costs in service_groups.items():
            aggregated_cost = self._aggregate_service(service, costs)
            aggregated.append(aggregated_cost)
        
        logger.info(f"Aggregated costs for {len(aggregated)} services")
        
        return aggregated
    
    def _aggregate_service(self, service: str, costs: List[ResourceCost]) -> AggregatedCost:
        """
        Aggregate costs for a single service.
        
        Args:
            service: Service name
            costs: Resource costs for this service
            
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
            group_by="service",
            group_value=service,
            scenario=scenario,
            diff=diff,
            resource_count=len(costs),
            confidence=confidence
        )
