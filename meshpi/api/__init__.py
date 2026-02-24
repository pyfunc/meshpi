"""
meshpi.api
==========
FastAPI routes for MeshPi host service.
"""

from .monitoring import router as monitoring_router

__all__ = ["monitoring_router"]