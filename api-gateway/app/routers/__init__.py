"""Routers package."""

from .health import router as health_router
from .uploads import router as uploads_router
from .jobs import router as jobs_router

__all__ = [
    "health_router",
    "uploads_router",
    "jobs_router",
]
