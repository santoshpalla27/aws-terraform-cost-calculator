from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes
from app.services.registry import ServiceRegistry
from app.services.ec2 import EC2Service
from app.services.s3 import S3Service
from app.services.aws_lambda import LambdaService

app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    # Register Services
    registry = ServiceRegistry.get_instance()
    registry.register("aws_instance", EC2Service)
    registry.register("aws_s3_bucket", S3Service)
    registry.register("aws_lambda_function", LambdaService)

app.include_router(routes.router)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "CloudCost Backend is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
