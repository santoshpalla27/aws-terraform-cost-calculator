"""
Internal API endpoints for plan interpretation.
"""
from fastapi import APIRouter, HTTPException, status
from app.schemas.api import InterpretRequest, InterpretResponse
from app.interpreter.nrg_builder import interpret_plan
from app.utils.plan_loader import PlanLoader
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post(
    "/interpret",
    response_model=InterpretResponse,
    status_code=status.HTTP_200_OK,
    summary="Interpret Terraform plan JSON",
    description="Parse terraform show -json output and produce Normalized Resource Graph"
)
async def interpret_terraform_plan(request: InterpretRequest) -> InterpretResponse:
    """
    Interpret Terraform plan and produce NRG.
    
    This is a pure CPU-bound operation with no side effects.
    """
    logger.info(
        "Received interpretation request",
        extra={'plan_json_reference': request.plan_json_reference}
    )
    
    try:
        # Load plan JSON from reference
        plan_json = PlanLoader.load(request.plan_json_reference)
        
        logger.info(f"Loaded plan JSON ({len(str(plan_json))} bytes)")
        
        # Build NRG from plan JSON
        nrg = interpret_plan(plan_json)
        
        logger.info(
            "Interpretation complete",
            extra={
                'total_resources': nrg.metadata.total_resources,
                'unknown_count': nrg.metadata.unknown_value_count,
                'total_dependencies': sum(len(node.dependencies) for node in nrg.nodes)
            }
        )
        
        return InterpretResponse(
            normalized_resource_graph=[node.model_dump() for node in nrg.nodes],
            interpretation_metadata=nrg.metadata.model_dump()
        )
    
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Invalid plan reference: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid plan reference: {str(e)}"
        )
    
    except KeyError as e:
        logger.error(f"Invalid plan JSON structure: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid plan JSON structure: missing key {e}"
        )
    
    except Exception as e:
        logger.error(f"Interpretation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Interpretation failed: {str(e)}"
        )


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check"
)
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "plan-interpreter"}
