"""
Cost service orchestrator.
"""
from typing import Dict, Any, List
from decimal import Decimal
import hashlib
import json
from app.schemas.cost import (
    ResourceCost,
    CostDimension,
    AggregateRequest,
    AggregateResponse,
    FCM,
    ConfidenceLevel
)
from app.calculation.cost_calculator import CostCalculator
from app.calculation.scenario_calculator import ScenarioCalculator
from app.calculation.confidence_calculator import ConfidenceCalculator
from app.aggregation.service_aggregator import ServiceAggregator
from app.aggregation.region_aggregator import RegionAggregator
from app.analysis.diff_calculator import DiffCalculator
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CostService:
    """Orchestrates cost aggregation."""
    
    def __init__(self, default_currency: str = "USD", enable_determinism_hash: bool = True):
        """
        Initialize cost service.
        
        Args:
            default_currency: Default currency
            enable_determinism_hash: Enable determinism hash calculation
        """
        self.default_currency = default_currency
        self.enable_determinism_hash = enable_determinism_hash
        
        self.cost_calc = CostCalculator(default_currency)
        self.scenario_calc = ScenarioCalculator(default_currency)
        self.confidence_calc = ConfidenceCalculator()
        self.service_agg = ServiceAggregator(default_currency)
        self.region_agg = RegionAggregator(default_currency)
        self.diff_calc = DiffCalculator()
    
    async def aggregate_costs(self, request: AggregateRequest) -> AggregateResponse:
        """
        Aggregate costs from ERG, pricing, and usage.
        
        Args:
            request: Aggregation request
            
        Returns:
            Final Cost Model
        """
        logger.info(
            f"Aggregating costs: {len(request.resources)} resources, "
            f"{len(request.pricing_records)} pricing records, "
            f"{len(request.usage_records)} usage records"
        )
        
        # Build resource costs
        resource_costs = []
        
        for resource in request.resources:
            try:
                resource_cost = self._calculate_resource_cost(
                    resource,
                    request.pricing_records,
                    request.usage_records
                )
                resource_costs.append(resource_cost)
            except Exception as e:
                logger.error(f"Failed to calculate cost for resource {resource.get('resource_id')}: {e}")
                # Continue processing other resources
        
        # Aggregate by service
        aggregated_by_service = self.service_agg.aggregate_by_service(resource_costs)
        
        # Aggregate by region
        aggregated_by_region = self.region_agg.aggregate_by_region(resource_costs)
        
        # Calculate total cost
        total_cost = self._calculate_total_cost(resource_costs)
        
        # Calculate total diff
        total_diff = self.diff_calc.calculate_diff(total_cost)
        
        # Calculate overall confidence
        overall_confidence = self.confidence_calc.aggregate_confidence(
            [rc.confidence for rc in resource_costs]
        )
        
        # Calculate determinism hash
        determinism_hash = None
        if self.enable_determinism_hash:
            determinism_hash = self._calculate_determinism_hash(resource_costs)
        
        # Build FCM
        fcm = FCM(
            resource_costs=resource_costs,
            aggregated_by_service=aggregated_by_service,
            aggregated_by_region=aggregated_by_region,
            total_cost=total_cost,
            total_diff=total_diff,
            overall_confidence=overall_confidence,
            determinism_hash=determinism_hash
        )
        
        logger.info(
            f"Aggregation complete: {len(resource_costs)} resources, "
            f"total expected cost: ${total_cost.expected}, "
            f"confidence: {overall_confidence}"
        )
        
        return AggregateResponse(fcm=fcm)
    
    def _calculate_resource_cost(
        self,
        resource: Dict[str, Any],
        pricing_records: List[Dict[str, Any]],
        usage_records: List[Dict[str, Any]]
    ) -> ResourceCost:
        """
        Calculate cost for a single resource.
        
        Args:
            resource: Resource data
            pricing_records: Pricing records
            usage_records: Usage records
            
        Returns:
            Resource cost
        """
        resource_id = resource.get('resource_id', 'unknown')
        
        # Find pricing for this resource
        pricing = self._find_pricing_for_resource(resource_id, pricing_records)
        
        # Find usage for this resource
        usage = self._find_usage_for_resource(resource_id, usage_records)
        
        # Calculate cost dimensions
        dimensions = []
        
        # For simplicity, assume one dimension (can be extended)
        if pricing and usage:
            # Extract values (simplified - real implementation would handle multiple dimensions)
            unit_price = Decimal(str(pricing.get('unit_price', 0)))
            usage_min = Decimal(str(usage.get('usage_min', 0)))
            usage_expected = Decimal(str(usage.get('usage_expected', 0)))
            usage_max = Decimal(str(usage.get('usage_max', 0)))
            unit = usage.get('unit', 'hours')
            dimension_name = usage.get('dimension', 'default')
            
            # Calculate costs for each scenario
            cost_min = usage_min * unit_price
            cost_expected = usage_expected * unit_price
            cost_max = usage_max * unit_price
            
            # Create dimension for expected scenario
            dimension = CostDimension(
                dimension=dimension_name,
                usage_units=usage_expected,
                unit_price=unit_price,
                cost=cost_expected,
                unit=unit,
                currency=self.default_currency
            )
            dimensions.append(dimension)
        else:
            # No pricing or usage - zero cost
            cost_min = cost_expected = cost_max = Decimal('0')
        
        # Create scenario
        scenario = self.scenario_calc.create_scenario(
            cost_min,
            cost_expected,
            cost_max,
            self.default_currency
        )
        
        # Calculate diff
        diff = self.diff_calc.calculate_diff(scenario)
        
        # Calculate confidence
        pricing_conf = pricing.get('confidence', 'LOW') if pricing else 'LOW'
        usage_conf = usage.get('confidence', 'LOW') if usage else 'LOW'
        confidence = self.confidence_calc.propagate_confidence(pricing_conf, usage_conf)
        
        return ResourceCost(
            resource_id=resource_id,
            resource_type=resource.get('resource_type', 'unknown'),
            service=resource.get('service', 'unknown'),
            region=resource.get('region', 'unknown'),
            dimensions=dimensions,
            scenario=scenario,
            diff=diff,
            confidence=confidence,
            confidence_sources={
                'pricing': pricing_conf,
                'usage': usage_conf
            }
        )
    
    def _find_pricing_for_resource(
        self,
        resource_id: str,
        pricing_records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Find pricing record for resource."""
        for record in pricing_records:
            if record.get('resource_id') == resource_id:
                return record
        return None
    
    def _find_usage_for_resource(
        self,
        resource_id: str,
        usage_records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Find usage record for resource."""
        for record in usage_records:
            if record.get('resource_id') == resource_id:
                return record
        return None
    
    def _calculate_total_cost(self, resource_costs: List[ResourceCost]):
        """Calculate total cost across all resources."""
        total_min = Decimal('0')
        total_expected = Decimal('0')
        total_max = Decimal('0')
        
        for cost in resource_costs:
            total_min += cost.scenario.min
            total_expected += cost.scenario.expected
            total_max += cost.scenario.max
        
        return self.scenario_calc.create_scenario(
            total_min,
            total_expected,
            total_max,
            self.default_currency
        )
    
    def _calculate_determinism_hash(self, resource_costs: List[ResourceCost]) -> str:
        """Calculate determinism hash for verification."""
        # Create deterministic representation
        data = {
            'resource_costs': [
                {
                    'resource_id': rc.resource_id,
                    'min': str(rc.scenario.min),
                    'expected': str(rc.scenario.expected),
                    'max': str(rc.scenario.max)
                }
                for rc in sorted(resource_costs, key=lambda x: x.resource_id)
            ]
        }
        
        # Calculate hash
        json_str = json.dumps(data, sort_keys=True)
        hash_obj = hashlib.sha256(json_str.encode())
        
        return hash_obj.hexdigest()[:16]
