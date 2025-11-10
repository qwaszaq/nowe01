"""
FastAPI Dependency Injection Functions
Provides singleton instances and shared dependencies for API routes
"""

from functools import lru_cache
from typing import Annotated
from fastapi import Depends, Query
import logging

from src.config.settings import Settings, settings
from src.storage.postgres_store import PostgresStore
from src.storage.redis_store import RedisStore
from src.storage.qdrant_store import QdrantStore
from src.storage.elastic_store import ElasticStore
from src.orchestration.document_processor import DocumentProcessor
from src.orchestration.analysis_flow import AnalysisFlow
from src.orchestration.state_manager import StateManager
from src.api.models import PaginationParams

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION DEPENDENCIES
# ============================================================================

@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings (cached singleton)

    Returns:
        Settings: Application configuration loaded from environment variables

    Example:
        >>> @app.get("/config")
        >>> async def get_config(settings: Settings = Depends(get_settings)):
        >>>     return {"app_name": settings.app_name}
    """
    logger.debug("Loading application settings")
    return settings


# ============================================================================
# STORAGE LAYER DEPENDENCIES
# ============================================================================

@lru_cache()
def get_postgres_store() -> PostgresStore:
    """
    Get PostgreSQL storage instance (cached singleton)

    Returns:
        PostgresStore: Initialized PostgreSQL connection pool

    Example:
        >>> @app.get("/cases")
        >>> async def list_cases(
        >>>     db: PostgresStore = Depends(get_postgres_store)
        >>> ):
        >>>     cases = db.list_cases()
        >>>     return cases

    Notes:
        - Connection pool is initialized on first call
        - Subsequent calls return the same instance
        - Thread-safe connection pooling is handled internally
    """
    logger.debug("Initializing PostgresStore singleton")
    return PostgresStore()


@lru_cache()
def get_redis_store() -> RedisStore:
    """
    Get Redis cache instance (cached singleton)

    Returns:
        RedisStore: Initialized Redis connection pool

    Example:
        >>> @app.get("/metrics/{document_id}")
        >>> async def get_metrics(
        >>>     document_id: UUID,
        >>>     cache: RedisStore = Depends(get_redis_store)
        >>> ):
        >>>     cached = cache.get(f"metrics:{document_id}")
        >>>     if cached:
        >>>         return json.loads(cached)
        >>>     # ... fetch from database ...

    Notes:
        - Gracefully handles Redis unavailability
        - Returns None for cache operations if Redis is down
        - Connection pool is shared across all requests
    """
    logger.debug("Initializing RedisStore singleton")
    return RedisStore()


@lru_cache()
def get_qdrant_store() -> QdrantStore:
    """
    Get Qdrant vector store instance (cached singleton)

    Returns:
        QdrantStore: Initialized Qdrant client

    Example:
        >>> @app.post("/search")
        >>> async def search_documents(
        >>>     query_embedding: List[float],
        >>>     vector_db: QdrantStore = Depends(get_qdrant_store)
        >>> ):
        >>>     results = vector_db.search_chunks(
        >>>         query_embedding=query_embedding,
        >>>         limit=10
        >>>     )
        >>>     return results

    Notes:
        - Collections are automatically created on initialization
        - Client maintains persistent connection to Qdrant server
    """
    logger.debug("Initializing QdrantStore singleton")
    return QdrantStore()


@lru_cache()
def get_elasticsearch_store() -> ElasticStore:
    """
    Get Elasticsearch store instance (cached singleton)

    Returns:
        ElasticStore: Initialized Elasticsearch client

    Example:
        >>> @app.get("/search/fulltext")
        >>> async def fulltext_search(
        >>>     query: str,
        >>>     search: ElasticStore = Depends(get_elasticsearch_store)
        >>> ):
        >>>     results = search.search(
        >>>         query=query,
        >>>         limit=10
        >>>     )
        >>>     return results

    Notes:
        - Indexes are automatically created on initialization
        - Gracefully handles Elasticsearch unavailability
        - Returns empty results if Elasticsearch is down
    """
    logger.debug("Initializing ElasticStore singleton")
    return ElasticStore()


# ============================================================================
# ORCHESTRATION LAYER DEPENDENCIES
# ============================================================================

@lru_cache()
def get_document_processor() -> DocumentProcessor:
    """
    Get document processor instance (cached singleton)

    Returns:
        DocumentProcessor: Initialized document processing pipeline

    Example:
        >>> @app.post("/documents/{document_id}/process")
        >>> async def process_document(
        >>>     document_id: UUID,
        >>>     case_id: UUID,
        >>>     processor: DocumentProcessor = Depends(get_document_processor)
        >>> ):
        >>>     result = await processor.process_document(
        >>>         case_id=case_id,
        >>>         document_path=f"/data/uploads/{document_id}.pdf",
        >>>         document_metadata={"document_id": document_id}
        >>>     )
        >>>     return result

    Notes:
        - Orchestrates PDF extraction, chunking, embedding, and storage
        - All storage dependencies are automatically injected
        - State tracking handled internally via Redis
        - Processing is async and can take several minutes
    """
    logger.debug("Initializing DocumentProcessor singleton")
    return DocumentProcessor(
        pdf_processor=None,  # Will auto-create
        text_chunker=None,   # Will auto-create
        embeddings=None,     # Will auto-create
        qdrant_store=get_qdrant_store(),
        postgres_store=get_postgres_store(),
        redis_store=get_redis_store()
    )


@lru_cache()
def get_analysis_flow() -> AnalysisFlow:
    """
    Get analysis flow orchestrator instance (cached singleton)

    Returns:
        AnalysisFlow: Initialized analysis pipeline orchestrator

    Example:
        >>> @app.post("/documents/{document_id}/analyze")
        >>> async def analyze_document(
        >>>     document_id: UUID,
        >>>     analysis_type: str = "comprehensive",
        >>>     flow: AnalysisFlow = Depends(get_analysis_flow)
        >>> ):
        >>>     result = await flow.analyze_document(
        >>>         document_id=document_id,
        >>>         analysis_type=analysis_type
        >>>     )
        >>>     return result

    Notes:
        - Coordinates semantic search, financial calculations, and micro-agents
        - Results are automatically cached in Redis
        - Supports multiple analysis types: comprehensive, liquidity, profitability, leverage
        - Quality scores calculated based on data completeness
    """
    logger.debug("Initializing AnalysisFlow singleton")

    # Import here to avoid circular dependencies
    from src.core.search.semantic_search import SemanticSearch
    from src.core.llm.micro_agents import MicroAgents

    # Create dependencies
    semantic_search = SemanticSearch(
        embeddings=None,  # Will auto-create E5Embeddings
        qdrant_store=get_qdrant_store()
    )

    micro_agents = MicroAgents(
        llm_client=None  # Will auto-create LLMClient
    )

    return AnalysisFlow(
        semantic_search=semantic_search,
        micro_agents=micro_agents,
        postgres_store=get_postgres_store(),
        redis_store=get_redis_store()
    )


@lru_cache()
def get_state_manager() -> StateManager:
    """
    Get state manager instance (cached singleton)

    Returns:
        StateManager: Initialized state tracking manager

    Example:
        >>> @app.get("/documents/{document_id}/status")
        >>> async def get_document_status(
        >>>     document_id: UUID,
        >>>     state_mgr: StateManager = Depends(get_state_manager)
        >>> ):
        >>>     state = state_mgr.get_document_state(document_id)
        >>>     if state:
        >>>         return {
        >>>             "status": state.state.value,
        >>>             "progress": state.progress_percent,
        >>>             "stage": state.current_stage
        >>>         }
        >>>     return {"error": "Document not found"}

    Notes:
        - Tracks document processing and analysis workflow states
        - Uses Redis for fast state lookups with PostgreSQL fallback
        - Validates state transitions automatically
        - Emits events via Redis pub/sub for real-time monitoring
    """
    logger.debug("Initializing StateManager singleton")
    return StateManager(
        redis_store=get_redis_store(),
        postgres_store=get_postgres_store()
    )


# ============================================================================
# PAGINATION DEPENDENCIES
# ============================================================================

def get_pagination_params(
    page: int = Query(
        default=1,
        ge=1,
        description="Page number (starting from 1)"
    ),
    page_size: int = Query(
        default=50,
        ge=1,
        le=100,
        description="Number of items per page (max 100)"
    )
) -> PaginationParams:
    """
    Get pagination parameters from query string

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page (1-100)

    Returns:
        PaginationParams: Pagination parameters with calculated offset

    Example:
        >>> @app.get("/cases")
        >>> async def list_cases(
        >>>     pagination: PaginationParams = Depends(get_pagination_params),
        >>>     db: PostgresStore = Depends(get_postgres_store)
        >>> ):
        >>>     cases = db.list_cases(
        >>>         limit=pagination.limit,
        >>>         offset=pagination.offset
        >>>     )
        >>>     total = db.count_cases()
        >>>     return PaginatedResponse.create(
        >>>         items=cases,
        >>>         total=total,
        >>>         page=pagination.page,
        >>>         page_size=pagination.page_size
        >>>     )

    Notes:
        - Automatically validates page and page_size ranges
        - Provides convenient offset/limit properties
        - Default: page=1, page_size=50
        - Max page_size: 100
    """
    return PaginationParams(page=page, page_size=page_size)


# ============================================================================
# TYPED DEPENDENCY ANNOTATIONS
# ============================================================================

# These type annotations can be used in route functions for cleaner syntax
# Example: async def my_route(db: PostgresStoreType, cache: RedisStoreType)

PostgresStoreType = Annotated[PostgresStore, Depends(get_postgres_store)]
RedisStoreType = Annotated[RedisStore, Depends(get_redis_store)]
QdrantStoreType = Annotated[QdrantStore, Depends(get_qdrant_store)]
ElasticStoreType = Annotated[ElasticStore, Depends(get_elasticsearch_store)]
DocumentProcessorType = Annotated[DocumentProcessor, Depends(get_document_processor)]
AnalysisFlowType = Annotated[AnalysisFlow, Depends(get_analysis_flow)]
StateManagerType = Annotated[StateManager, Depends(get_state_manager)]
PaginationType = Annotated[PaginationParams, Depends(get_pagination_params)]
SettingsType = Annotated[Settings, Depends(get_settings)]


# ============================================================================
# USAGE EXAMPLES IN ROUTES
# ============================================================================

"""
EXAMPLE 1: Simple CRUD endpoint with database dependency
---------------------------------------------------------

from fastapi import APIRouter, HTTPException
from uuid import UUID
from src.api.dependencies import PostgresStoreType
from src.api.models import CaseResponse

router = APIRouter(prefix="/api/v1/cases", tags=["cases"])

@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: UUID,
    db: PostgresStoreType
) -> CaseResponse:
    \"\"\"Get case by ID\"\"\"
    case = db.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return CaseResponse(**case)


EXAMPLE 2: Paginated list endpoint
-----------------------------------

from src.api.dependencies import PostgresStoreType, PaginationType
from src.api.models import PaginatedResponse, CaseResponse

@router.get("/", response_model=PaginatedResponse[CaseResponse])
async def list_cases(
    db: PostgresStoreType,
    pagination: PaginationType,
    status: Optional[str] = None
) -> PaginatedResponse[CaseResponse]:
    \"\"\"List all cases with pagination\"\"\"
    cases = db.list_cases(
        status=status,
        limit=pagination.limit,
        offset=pagination.offset
    )

    # Convert to response models
    case_responses = [CaseResponse(**case) for case in cases]

    # Get total count for pagination
    with db.get_cursor() as cursor:
        if status:
            cursor.execute("SELECT COUNT(*) FROM cases WHERE status = %s", (status,))
        else:
            cursor.execute("SELECT COUNT(*) FROM cases")
        total = cursor.fetchone()['count']

    return PaginatedResponse.create(
        items=case_responses,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size
    )


EXAMPLE 3: Document processing endpoint
----------------------------------------

from src.api.dependencies import DocumentProcessorType, StateManagerType
from src.api.models import MessageResponse

@router.post("/{document_id}/process", response_model=MessageResponse)
async def process_document(
    document_id: UUID,
    case_id: UUID,
    processor: DocumentProcessorType,
    state_mgr: StateManagerType
) -> MessageResponse:
    \"\"\"Process uploaded document\"\"\"
    try:
        # Get document from database
        document = processor.postgres_store.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Start processing (async background task)
        result = await processor.process_document(
            case_id=case_id,
            document_path=document['file_path'],
            document_metadata={"document_id": document_id}
        )

        if result.status == 'completed':
            return MessageResponse(
                message="Document processed successfully",
                detail=f"Processed {result.chunk_count} chunks in {result.elapsed_time:.2f}s"
            )
        else:
            return MessageResponse(
                message="Document processing failed",
                detail=result.error_message
            )

    except Exception as e:
        logger.error(f"Processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


EXAMPLE 4: Analysis endpoint with caching
------------------------------------------

from src.api.dependencies import AnalysisFlowType, RedisStoreType
from src.api.models import AnalysisResultResponse

@router.post("/{document_id}/analyze", response_model=AnalysisResultResponse)
async def analyze_document(
    document_id: UUID,
    analysis_type: str = "comprehensive",
    flow: AnalysisFlowType,
    cache: RedisStoreType
) -> AnalysisResultResponse:
    \"\"\"Run financial analysis on document\"\"\"
    try:
        # Check cache first
        cache_key = f"analysis:{document_id}:{analysis_type}"
        cached = cache.get(cache_key)

        if cached:
            logger.info(f"Serving cached analysis for {document_id}")
            result_dict = json.loads(cached)
            return AnalysisResultResponse(**result_dict)

        # Perform analysis
        result = await flow.analyze_document(
            document_id=document_id,
            analysis_type=analysis_type
        )

        # Convert to response model
        response = AnalysisResultResponse(
            document_id=result.document_id,
            analysis_type=result.analysis_type,
            status="completed",
            quality_score=result.quality_score,
            metrics_calculated=result.metrics.total_calculated,
            insights=asdict(result.insights),
            cached=result.cached
        )

        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Analysis failed")


EXAMPLE 5: Health check endpoint
---------------------------------

from src.api.dependencies import (
    PostgresStoreType,
    RedisStoreType,
    QdrantStoreType,
    SettingsType
)
from src.api.models import HealthCheckResponse, ComponentHealth

@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    settings: SettingsType,
    postgres: PostgresStoreType,
    redis: RedisStoreType,
    qdrant: QdrantStoreType
) -> HealthCheckResponse:
    \"\"\"Check system health\"\"\"
    components = {}

    # Check PostgreSQL
    pg_health = postgres.health_check()
    components["postgres"] = ComponentHealth(
        status=pg_health.get("status", "unknown"),
        details=pg_health,
        error=pg_health.get("error")
    )

    # Check Redis
    redis_health = redis.health_check()
    components["redis"] = ComponentHealth(
        status=redis_health.get("status", "unknown"),
        details=redis_health,
        error=redis_health.get("error")
    )

    # Check Qdrant
    qdrant_health = qdrant.health_check()
    components["qdrant"] = ComponentHealth(
        status=qdrant_health.get("status", "unknown"),
        details=qdrant_health,
        error=qdrant_health.get("error")
    )

    # Determine overall status
    statuses = [c.status for c in components.values()]
    if all(s == "healthy" for s in statuses):
        overall_status = "healthy"
    elif any(s == "unhealthy" for s in statuses):
        overall_status = "unhealthy"
    else:
        overall_status = "degraded"

    return HealthCheckResponse(
        status=overall_status,
        components=components,
        version=settings.app_version
    )
"""
