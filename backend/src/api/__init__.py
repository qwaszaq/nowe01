"""
FastAPI Application Factory
Main API application setup with routes, middleware, and error handlers
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from src.config.settings import settings
from src.api.routes import documents, analysis_router, cases
from src.api.routes import bi_analytics
from src.orchestration.analysis_flow import AnalysisFlow
from src.storage import PostgresStore

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"API available at: http://{settings.api_host}:{settings.api_port}{settings.api_prefix}")

    # Ensure upload directory exists
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Upload directory: {settings.upload_dir}")

    # Initialize analysis service
    try:
        from src.core.embeddings.e5_embeddings import E5Embeddings
        from src.core.llm.lm_studio_client import LMStudioClient
        from src.core.llm.micro_agents import MicroAgents
        from src.core.search.semantic_search import SemanticSearch
        from src.storage.qdrant_store import QdrantStore
        from src.storage.redis_store import RedisStore

        # Initialize stores
        postgres_store = PostgresStore()
        redis_store = RedisStore()

        # Initialize embedding service
        e5_embeddings = E5Embeddings()

        # Initialize vector store
        qdrant_store = QdrantStore()

        # Initialize semantic search
        semantic_search = SemanticSearch(e5_embeddings, qdrant_store)

        # Initialize LLM client and micro-agents
        llm_client = LMStudioClient()
        micro_agents = MicroAgents(redis_store, llm_client)

        # Initialize analysis flow orchestrator
        analysis_flow = AnalysisFlow(semantic_search, micro_agents, postgres_store, redis_store)

        # Set dependencies for analysis routes
        from src.api.routes import analysis
        analysis.set_dependencies(analysis_flow, postgres_store)

        logger.info("✓ Analysis service initialized")
    except Exception as e:
        logger.error(f"✗ Failed to initialize analysis service: {e}")

    yield

    # Shutdown
    logger.info("Shutting down application")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Investigation Intelligence Platform - Document Processing and Analysis API",
        docs_url=f"{settings.api_prefix}/docs",
        redoc_url=f"{settings.api_prefix}/redoc",
        openapi_url=f"{settings.api_prefix}/openapi.json",
        lifespan=lifespan
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(
        cases.router,
        prefix=settings.api_prefix
    )
    app.include_router(
        documents.router,
        prefix=settings.api_prefix
    )
    app.include_router(
        analysis_router,
        prefix=settings.api_prefix
    )
    app.include_router(
        bi_analytics.router,
        prefix=settings.api_prefix
    )

    # Exception handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors"""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation error",
                "detail": exc.errors(),
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle uncaught exceptions"""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "detail": str(exc) if settings.debug else "An unexpected error occurred"
            }
        )

    # Root endpoint
    @app.get("/")
    async def root():
        """API root endpoint"""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "status": "running",
            "docs": f"{settings.api_prefix}/docs"
        }

    # Health check
    @app.get(f"{settings.api_prefix}/health")
    async def health():
        """General health check"""
        return {
            "status": "healthy",
            "service": "investigation_platform",
            "version": settings.app_version
        }

    return app


# Application instance
app = create_app()
