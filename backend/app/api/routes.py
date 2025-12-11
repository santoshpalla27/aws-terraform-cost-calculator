import os
import shutil
import tempfile
import zipfile
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.engine.parser import HCLParser
from app.engine.pricing import PricingService
from app.services.registry import ServiceRegistry
from app.models.terraform import ProjectContext
from app.schemas.schemas import CostEstimateResponse, ResourceCost, CostItem

router = APIRouter()

@router.post("/scan", response_model=CostEstimateResponse)
async def scan_project(file: UploadFile = File(...)):
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip files are supported")

    # 1. Save and Unzip
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = os.path.join(temp_dir, file.filename)
        with open(zip_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
        except zipfile.BadZipFile:
            raise HTTPException(status_code=400, detail="Invalid zip file")

        # 2. Parse Terraform Project
        parser = HCLParser()
        context = parser.parse(temp_dir) # Recursive parse
        
        # 3. Calculate Costs
        pricing_service = PricingService()
        registry = ServiceRegistry.get_instance()
        
        total_hourly = 0.0
        total_monthly = 0.0
        resource_costs = []
        
        for address, resource in context.resources.items():
            service = registry.get_service(resource.type)
            if not service:
                # Skip unknown services for now, or mark as unsupported
                continue
                
            components = service.get_cost_components(resource, context)
            res_components = []
            res_total_hourly = 0.0
            res_total_monthly = 0.0
            
            for comp in components:
                # Get Price
                price_data = pricing_service.get_price(component_to_service_code(resource.type), comp.price_filter)
                
                unit_price = 0.0
                currency = "USD"
                attrs = {}
                
                if price_data:
                    unit_price = price_data.get("price", 0.0)
                    currency = price_data.get("currency", "USD")
                    attrs = price_data.get("attributes", {})
                
                hourly_cost = comp.hourly_quantity * unit_price
                monthly_cost = comp.monthly_quantity * unit_price
                
                res_total_hourly += hourly_cost
                res_total_monthly += monthly_cost
                
                res_components.append(CostItem(
                    name=comp.name,
                    unit=comp.unit,
                    hourly_quantity=comp.hourly_quantity,
                    monthly_quantity=comp.monthly_quantity,
                    price_per_unit=unit_price,
                    hourly_cost=hourly_cost,
                    monthly_cost=monthly_cost,
                    currency=currency,
                    attributes=attrs
                ))
            
            total_hourly += res_total_hourly
            total_monthly += res_total_monthly
            
            resource_costs.append(ResourceCost(
                address=address,
                type=resource.type,
                total_hourly_cost=res_total_hourly,
                total_monthly_cost=res_total_monthly,
                cost_components=res_components
            ))
            
        return CostEstimateResponse(
            total_hourly_cost=total_hourly,
            total_monthly_cost=total_monthly,
            currency="USD",
            resources=resource_costs,
            unresolved_variables=context.unresolved_variables
        )

def component_to_service_code(resource_type: str) -> str:
    """Helper to map TF type to AWS Service Code"""
    mapping = {
        "aws_instance": "AmazonEC2",
        "aws_s3_bucket": "AmazonS3",
        "aws_lambda_function": "AWSLambda"
    }
    return mapping.get(resource_type, "Unknown")
