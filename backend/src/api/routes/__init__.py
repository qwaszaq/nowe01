"""
API Routes Module
Centralizes all API endpoints
"""

from .cases import router as cases_router
from .analysis import router as analysis_router

__all__ = ["cases_router", "analysis_router"]
