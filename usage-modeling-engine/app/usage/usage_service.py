"""
Usage service orchestrator.
"""
from typing import Dict, Any, List
from app.schemas.usage import (
    UsageAnnotatedResource,
    UARG,
    UsageOverride,
    ApplyUsageRequest,
    ApplyUsageResponse
)
from app.usage.profile_loader import ProfileLoader
from app.usage.override_handler import OverrideHandler
from app.utils.logger import get_logger

logger = get_logger(__name__)


class UsageService:
    """Orchestrates usage application to resources."""
    
    def __init__(self, profile_loader: ProfileLoader):
        """
        Initialize usage service.
        
        Args:
            profile_loader: Profile loader instance
        """
        self.profile_loader = profile_loader
        self.usage_models = self._initialize_usage_models()
    
    def _initialize_usage_models(self) -> Dict[str, Any]:
        """Initialize usage models."""
        from app.usage_models.ec2 import EC2UsageModel
        from app.usage_models.ebs import EBSUsageModel
        
        models = {}
        
        # Register usage models
        for model_class in [EC2UsageModel, EBSUsageModel]:
            model = model_class()
            models[model.get_service_name()] = model
        
        logger.info(f"Initialized {len(models)} usage models: {list(models.keys())}")
        
        return models
    
    async def apply_usage(self, request: ApplyUsageRequest) -> ApplyUsageResponse:
        """
        Apply usage assumptions to resources.
        
        Args:
            request: Usage application request
            
        Returns:
            Usage application response with UARG
        """
        # Get profile
        profile_name = request.profile or self.profile_loader.list_profiles()[0]
        
        try:
            profile = self.profile_loader.get_profile(profile_name)
        except ValueError as e:
            logger.error(f"Profile not found: {e}")
            raise
        
        logger.info(f"Applying usage profile: {profile_name} (version: {profile.get('version')})")
        
        # Initialize override handler
        override_handler = OverrideHandler(request.overrides)
        
        # Process each resource
        annotated_resources = []
        
        for resource in request.resources:
            try:
                annotated_resource = self._apply_usage_to_resource(
                    resource,
                    profile,
                    override_handler
                )
                annotated_resources.append(annotated_resource)
                
            except Exception as e:
                logger.error(f"Failed to apply usage to resource {resource.get('resource_id')}: {e}")
                # Continue processing other resources
        
        # Build UARG
        uarg = UARG(
            resources=annotated_resources,
            profile_applied=profile_name,
            profile_version=profile.get('version', 'unknown'),
            overrides_count=len(request.overrides)
        )
        
        logger.info(
            f"Applied usage to {len(annotated_resources)} resources "
            f"(profile: {profile_name}, overrides: {len(request.overrides)})"
        )
        
        return ApplyUsageResponse(uarg=uarg)
    
    def _apply_usage_to_resource(
        self,
        resource: Dict[str, Any],
        profile: Dict[str, Any],
        override_handler: OverrideHandler
    ) -> UsageAnnotatedResource:
        """
        Apply usage to a single resource.
        
        Args:
            resource: Resource data
            profile: Usage profile
            override_handler: Override handler
            
        Returns:
            Usage-annotated resource
        """
        resource_id = resource.get('resource_id', 'unknown')
        service = resource.get('service', 'unknown')
        
        # Get usage model for service
        usage_model = self.usage_models.get(service)
        
        if not usage_model:
            logger.warning(f"No usage model for service: {service}, skipping resource {resource_id}")
            # Return resource with empty usage annotation
            from app.schemas.usage import UsageAnnotation, UsageConfidence
            usage_annotation = UsageAnnotation(
                usage_scenarios={},
                usage_profile=profile.get('name', 'unknown'),
                usage_confidence=UsageConfidence.LOW,
                usage_assumptions=["No usage model available for this service"],
                overrides_applied=[]
            )
        else:
            # Get overrides for this resource
            overrides = override_handler.get_overrides_for_resource(resource_id, service)
            
            # Apply usage model
            usage_annotation = usage_model.apply_usage(resource, profile, overrides)
        
        # Build annotated resource
        annotated_resource = UsageAnnotatedResource(
            resource_id=resource_id,
            resource_type=resource.get('resource_type', 'unknown'),
            service=service,
            region=resource.get('region', 'unknown'),
            attributes=resource.get('attributes', {}),
            usage_annotation=usage_annotation
        )
        
        return annotated_resource
