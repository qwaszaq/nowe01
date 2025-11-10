"""
FastAPI Main Application
Entry point for Investigation Intelligence Platform API
"""

import logging
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any
from datetime import datetime

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.config import settings
from src.storage import PostgresStore, QdrantStore, RedisStore
from src.storage.elastic_store import ElasticStore

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

def setup_logging():
    """Configure application logging"""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Set levels for specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured: level={settings.log_level}")
    return logger


logger = setup_logging()


# ============================================================================
# GLOBAL STORAGE INSTANCES
# ============================================================================

# These will be initialized in lifespan context manager
postgres_store: PostgresStore = None
qdrant_store: QdrantStore = None
redis_store: RedisStore = None
elastic_store: ElasticStore = None


# ============================================================================
# LIFESPAN CONTEXT MANAGER
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    Manages database connections and resource cleanup
    """
    # ========================================================================
    # STARTUP
    # ========================================================================
    logger.info("=" * 80)
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info("=" * 80)

    global postgres_store, qdrant_store, redis_store, elastic_store

    # Initialize PostgreSQL
    try:
        logger.info("Initializing PostgreSQL connection pool...")
        postgres_store = PostgresStore()
        health = postgres_store.health_check()
        if health['status'] == 'healthy':
            logger.info(f"✓ PostgreSQL connected: {health['database']}@{health['host']}")
        else:
            logger.error(f"✗ PostgreSQL unhealthy: {health.get('error')}")
    except Exception as e:
        logger.error(f"✗ PostgreSQL initialization failed: {e}")
        postgres_store = None

    # Initialize Qdrant
    try:
        logger.info("Initializing Qdrant vector store...")
        qdrant_store = QdrantStore()
        health = qdrant_store.health_check()
        if health['status'] == 'healthy':
            logger.info(f"✓ Qdrant connected: {health['collections_count']} collections")
        else:
            logger.error(f"✗ Qdrant unhealthy: {health.get('error')}")
    except Exception as e:
        logger.error(f"✗ Qdrant initialization failed: {e}")
        qdrant_store = None

    # Initialize Redis
    try:
        logger.info("Initializing Redis cache...")
        redis_store = RedisStore()
        health = redis_store.health_check()
        if health['status'] == 'healthy':
            logger.info(f"✓ Redis connected: {health['host']}:{health['port']}")
        else:
            logger.warning(f"⚠ Redis unavailable: {health.get('error')} (cache disabled)")
    except Exception as e:
        logger.warning(f"⚠ Redis initialization failed: {e} (cache disabled)")
        redis_store = None

    # Initialize Elasticsearch
    try:
        logger.info("Initializing Elasticsearch...")
        elastic_store = ElasticStore()
        health = elastic_store.health_check()
        if health['status'] in ['healthy', 'green', 'yellow']:
            logger.info(f"✓ Elasticsearch connected: {health.get('cluster_name', 'unknown')}")
        else:
            logger.warning(f"⚠ Elasticsearch unavailable: {health.get('error')} (search disabled)")
    except Exception as e:
        logger.warning(f"⚠ Elasticsearch initialization failed: {e} (search disabled)")
        elastic_store = None

    logger.info("=" * 80)
    logger.info(f"Application startup complete - listening on {settings.api_host}:{settings.api_port}")
    logger.info("=" * 80)

    # Make stores available to the app
    app.state.postgres = postgres_store
    app.state.qdrant = qdrant_store
    app.state.redis = redis_store
    app.state.elastic = elastic_store

    yield

    # ========================================================================
    # SHUTDOWN
    # ========================================================================
    logger.info("=" * 80)
    logger.info("Shutting down application...")
    logger.info("=" * 80)

    # Close all database connections
    if postgres_store:
        try:
            postgres_store.close()
            logger.info("✓ PostgreSQL connection pool closed")
        except Exception as e:
            logger.error(f"Error closing PostgreSQL: {e}")

    if qdrant_store:
        try:
            qdrant_store.close()
            logger.info("✓ Qdrant connection closed")
        except Exception as e:
            logger.error(f"Error closing Qdrant: {e}")

    if redis_store:
        try:
            redis_store.close()
            logger.info("✓ Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis: {e}")

    if elastic_store:
        try:
            elastic_store.close()
            logger.info("✓ Elasticsearch connection closed")
        except Exception as e:
            logger.error(f"Error closing Elasticsearch: {e}")

    logger.info("=" * 80)
    logger.info("Shutdown complete")
    logger.info("=" * 80)


# ============================================================================
# FASTAPI APPLICATION INITIALIZATION
# ============================================================================

app = FastAPI(
    title=settings.app_name,
    description="""
    ## Investigation Intelligence Platform API

    **Purpose**: AI-powered financial document analysis and investigation support

    **Features**:
    - Document upload and processing (PDF, DOCX)
    - Multi-language embedding with semantic search
    - Financial metrics extraction and calculation
    - Micro-agent powered analysis
    - Full-text and vector search capabilities

    **Architecture**:
    - **PostgreSQL**: Structured data (cases, documents, metrics, citations)
    - **Qdrant**: Vector embeddings for semantic search
    - **Redis**: Fast caching for micro-agents and embeddings
    - **Elasticsearch**: Full-text search and document discovery
    - **LM Studio**: Local LLM inference (micro-agents)

    **Tech Stack**: FastAPI, SQLAlchemy, Qdrant, Redis, Elasticsearch, pdfplumber
    """,
    version=settings.app_version,
    lifespan=lifespan,
    debug=settings.debug,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# ============================================================================
# MIDDLEWARE CONFIGURATION
# ============================================================================

# CORS Middleware - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if not settings.debug else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


# Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests with timing"""
    start_time = datetime.now()

    # Log request
    logger.info(f"→ {request.method} {request.url.path}")

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration_ms = (datetime.now() - start_time).total_seconds() * 1000

    # Log response
    logger.info(
        f"← {request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Duration: {duration_ms:.2f}ms"
    )

    return response


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    logger.warning(
        f"HTTP {exc.status_code}: {exc.detail} - "
        f"Path: {request.url.path}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path,
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    logger.warning(
        f"Validation error on {request.url.path}: {exc.errors()}"
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "details": exc.errors(),
            "body": exc.body,
            "path": request.url.path,
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all uncaught exceptions"""
    logger.error(
        f"Unhandled exception on {request.url.path}: {exc}",
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": str(exc) if settings.debug else "An unexpected error occurred",
            "path": request.url.path,
            "timestamp": datetime.now().isoformat()
        }
    )


# ============================================================================
# CORE ENDPOINTS
# ============================================================================

@app.get(
    "/",
    tags=["Core"],
    summary="API Information",
    description="Get API metadata and available endpoints"
)
async def root() -> Dict[str, Any]:
    """
    Root endpoint - returns API information

    Returns:
        API metadata including version, status, and available endpoints
    """
    return {
        "api": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "debug_mode": settings.debug,
        "timestamp": datetime.now().isoformat(),
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_schema": "/openapi.json"
        },
        "endpoints": {
            "health": "/api/health",
            "cases": f"{settings.api_prefix}/cases",
            "documents": f"{settings.api_prefix}/documents",
            "analysis": f"{settings.api_prefix}/analysis",
            "search": f"{settings.api_prefix}/search"
        },
        "databases": {
            "postgres": {
                "host": settings.postgres_host,
                "database": settings.postgres_db,
                "status": "connected" if postgres_store else "disconnected"
            },
            "qdrant": {
                "host": settings.qdrant_host,
                "port": settings.qdrant_port,
                "status": "connected" if qdrant_store else "disconnected"
            },
            "redis": {
                "host": settings.redis_host,
                "port": settings.redis_port,
                "status": "connected" if redis_store else "disconnected"
            },
            "elasticsearch": {
                "host": settings.elastic_host,
                "port": settings.elastic_port,
                "status": "connected" if elastic_store else "disconnected"
            }
        }
    }


@app.get(
    "/api/health",
    tags=["Core"],
    summary="Health Check",
    description="Check health status of all database connections"
)
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint - verifies all database connections

    Checks:
    - PostgreSQL connection and query execution
    - Qdrant vector store connectivity
    - Redis cache availability
    - Elasticsearch cluster health

    Returns:
        Overall health status and individual database health checks
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": settings.app_version,
        "databases": {}
    }

    # Check PostgreSQL
    if postgres_store:
        try:
            pg_health = postgres_store.health_check()
            health_status["databases"]["postgres"] = pg_health
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            health_status["databases"]["postgres"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"
    else:
        health_status["databases"]["postgres"] = {
            "status": "unavailable",
            "error": "Not initialized"
        }
        health_status["status"] = "degraded"

    # Check Qdrant
    if qdrant_store:
        try:
            qdrant_health = qdrant_store.health_check()
            health_status["databases"]["qdrant"] = qdrant_health
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            health_status["databases"]["qdrant"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"
    else:
        health_status["databases"]["qdrant"] = {
            "status": "unavailable",
            "error": "Not initialized"
        }
        health_status["status"] = "degraded"

    # Check Redis (optional - won't mark as degraded if unavailable)
    if redis_store:
        try:
            redis_health = redis_store.health_check()
            health_status["databases"]["redis"] = redis_health
        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
            health_status["databases"]["redis"] = {
                "status": "unavailable",
                "error": str(e)
            }
    else:
        health_status["databases"]["redis"] = {
            "status": "unavailable",
            "error": "Not initialized (cache disabled)"
        }

    # Check Elasticsearch (optional - won't mark as degraded if unavailable)
    if elastic_store:
        try:
            elastic_health = elastic_store.health_check()
            health_status["databases"]["elasticsearch"] = elastic_health
        except Exception as e:
            logger.warning(f"Elasticsearch health check failed: {e}")
            health_status["databases"]["elasticsearch"] = {
                "status": "unavailable",
                "error": str(e)
            }
    else:
        health_status["databases"]["elasticsearch"] = {
            "status": "unavailable",
            "error": "Not initialized (search disabled)"
        }

    # Set overall status based on critical services (Postgres + Qdrant)
    critical_services_healthy = (
        health_status["databases"]["postgres"]["status"] == "healthy" and
        health_status["databases"]["qdrant"]["status"] == "healthy"
    )

    if not critical_services_healthy:
        health_status["status"] = "unhealthy"

    return health_status


# ============================================================================
# ROUTER IMPORTS (Prepared for future implementation)
# ============================================================================

# TODO: Implement API routes
# from src.api.routes.cases import router as cases_router
# from src.api.routes.documents import router as documents_router
# from src.api.routes.analysis import router as analysis_router
# from src.api.routes.search import router as search_router
#
# app.include_router(cases_router, prefix=settings.api_prefix, tags=["Cases"])
# app.include_router(documents_router, prefix=settings.api_prefix, tags=["Documents"])
# app.include_router(analysis_router, prefix=settings.api_prefix, tags=["Analysis"])
# app.include_router(search_router, prefix=settings.api_prefix, tags=["Search"])


# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True
    )
