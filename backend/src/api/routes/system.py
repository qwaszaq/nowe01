"""
System Management REST API Endpoints
Provides system-level operations like service reinitialization
"""

import logging
from datetime import datetime

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/system", tags=["system"])


@router.post(
    "/reinitialize",
    summary="Reinitialize All Services",
    description="Triggers reinitialization of all backend services (Analysis Flow, embeddings, etc.)"
)
async def reinitialize_services():
    """
    Reinitialize all backend services

    This endpoint triggers a reinitialization of:
    - E5 Embeddings
    - Semantic Search
    - LM Studio Client
    - Micro Agents
    - Analysis Flow

    Returns:
        Success message with timestamp
    """
    try:
        logger.info("=" * 80)
        logger.info("SERVICE REINITIALIZATION REQUESTED")
        logger.info("=" * 80)

        # Import here to access the app state
        from src.api.main import app
        from src.orchestration.analysis_flow import AnalysisFlow
        from src.core.search.semantic_search import SemanticSearch
        from src.core.embeddings.e5_embeddings import E5Embeddings
        from src.core.llm.micro_agents import MicroAgents
        from src.core.llm.lm_studio_client import LMStudioClient
        from src.api.routes import analysis as analysis_routes
        from src.config import settings

        # Get storage instances from app state
        postgres_store = app.state.postgres
        qdrant_store = app.state.qdrant
        redis_store = app.state.redis

        # Initialize E5 Embeddings
        logger.info("Reinitializing E5 Embeddings...")
        e5_embeddings = E5Embeddings(
            endpoint=settings.llm_endpoint,
            model=settings.embedding_model,
            dimensions=settings.embedding_dimension,
            timeout=60,
            max_retries=3
        )
        logger.info("✓ E5 Embeddings reinitialized")

        # Initialize SemanticSearch
        logger.info("Reinitializing Semantic Search...")
        semantic_search = SemanticSearch(
            embeddings_service=e5_embeddings,
            qdrant_store=qdrant_store
        )
        logger.info("✓ Semantic Search reinitialized")

        # Initialize LM Studio Client
        logger.info("Reinitializing LM Studio Client...")
        llm_client = LMStudioClient(
            endpoint=settings.llm_endpoint,
            timeout=settings.llm_timeout,
            max_retries=settings.llm_max_retries
        )
        logger.info("✓ LM Studio Client reinitialized")

        # Initialize MicroAgents
        logger.info("Reinitializing Micro Agents...")
        micro_agents = MicroAgents(redis_client=redis_store, llm_client=llm_client)
        logger.info("✓ Micro Agents reinitialized")

        # Initialize AnalysisFlow
        logger.info("Reinitializing Analysis Flow...")
        analysis_flow = AnalysisFlow(
            semantic_search=semantic_search,
            micro_agents=micro_agents,
            postgres_store=postgres_store,
            redis_store=redis_store
        )
        logger.info("✓ Analysis Flow reinitialized")

        # Update app state
        app.state.analysis_flow = analysis_flow

        # Inject dependencies into analysis routes
        analysis_routes.set_dependencies(
            analysis_flow=analysis_flow,
            postgres_store=postgres_store
        )
        logger.info("✓ Analysis routes dependencies updated")

        logger.info("=" * 80)
        logger.info("SERVICE REINITIALIZATION COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "All services reinitialized successfully",
                "timestamp": datetime.now().isoformat(),
                "services": [
                    "E5 Embeddings",
                    "Semantic Search",
                    "LM Studio Client",
                    "Micro Agents",
                    "Analysis Flow"
                ]
            }
        )

    except Exception as e:
        logger.error(f"Service reinitialization failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": f"Service reinitialization failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )
