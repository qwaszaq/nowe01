"""
Financial Analysis REST API Endpoints
Provides comprehensive financial analysis capabilities including:
- Document analysis with multiple analysis types
- Cached results retrieval
- Semantic search across documents
- Metrics and insights extraction
"""

import logging
import time
from typing import List, Optional, Literal, Dict, Any
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Path, status
from pydantic import BaseModel, Field, validator

from src.orchestration.analysis_flow import (
    AnalysisFlow,
    AnalysisResult,
    MetricResult,
    InsightsResult,
    SearchResult
)
from src.storage.postgres_store import PostgresStore
from src.storage.redis_store import RedisStore

logger = logging.getLogger(__name__)

# ============================================================================
# ROUTER SETUP
# ============================================================================

router = APIRouter(
    prefix="/analysis",
    tags=["analysis"],
    responses={
        404: {"description": "Document or resource not found"},
        500: {"description": "Internal server error"}
    }
)

# Global state - will be initialized in main app
_analysis_flow: Optional[AnalysisFlow] = None
_postgres_store: Optional[PostgresStore] = None


def set_dependencies(
    analysis_flow: AnalysisFlow,
    postgres_store: PostgresStore
):
    """
    Set dependencies for the analysis router

    Args:
        analysis_flow: Initialized AnalysisFlow orchestrator
        postgres_store: Initialized PostgresStore instance
    """
    global _analysis_flow, _postgres_store
    _analysis_flow = analysis_flow
    _postgres_store = postgres_store
    logger.info("Analysis API dependencies initialized")


# ============================================================================
# PYDANTIC REQUEST/RESPONSE MODELS
# ============================================================================

class AnalysisRequest(BaseModel):
    """Request model for document analysis"""
    document_id: UUID = Field(
        ...,
        description="UUID of the document to analyze"
    )
    analysis_type: Literal[
        "comprehensive",
        "liquidity",
        "profitability",
        "leverage",
        "quick"
    ] = Field(
        default="comprehensive",
        description="Type of financial analysis to perform"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "550e8400-e29b-41d4-a716-446655440000",
                "analysis_type": "comprehensive"
            }
        }


class MetricResponse(BaseModel):
    """Individual financial metric response"""
    metric_name: str = Field(
        ...,
        description="Name of the financial metric (e.g., 'current_ratio')"
    )
    metric_value: Optional[float] = Field(
        None,
        description="Calculated value of the metric"
    )
    metric_unit: Optional[str] = Field(
        None,
        description="Unit of measurement (e.g., 'ratio', 'percent')"
    )
    interpretation: str = Field(
        ...,
        description="Human-readable interpretation of the metric"
    )
    category: str = Field(
        ...,
        description="Category of metric (liquidity, profitability, leverage)"
    )
    citations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Source citations with page numbers and formulas"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "metric_name": "current_ratio",
                "metric_value": 2.15,
                "metric_unit": "ratio",
                "interpretation": "Strong liquidity - company can cover short-term obligations 2.15x",
                "category": "liquidity",
                "citations": [
                    {
                        "page_numbers": [5],
                        "formula": "Current Assets / Current Liabilities"
                    }
                ]
            }
        }


class InsightResponse(BaseModel):
    """AI-generated insights response"""
    risk_assessment: str = Field(
        ...,
        description="Overall risk level (low, medium, high, insufficient_data)"
    )
    liquidity_position: str = Field(
        ...,
        description="Liquidity assessment (strong, adequate, weak, insufficient_data)"
    )
    profitability_trends: str = Field(
        ...,
        description="Profitability trend analysis"
    )
    leverage_analysis: str = Field(
        ...,
        description="Debt/leverage assessment"
    )
    overall_health: str = Field(
        ...,
        description="Overall financial health (excellent, good, fair, poor, insufficient_data)"
    )
    key_concerns: List[str] = Field(
        default_factory=list,
        description="List of key financial concerns identified"
    )
    key_strengths: List[str] = Field(
        default_factory=list,
        description="List of key financial strengths identified"
    )
    classification_count: int = Field(
        ...,
        description="Number of micro-agent classifications performed"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "risk_assessment": "low",
                "liquidity_position": "strong",
                "profitability_trends": "stable",
                "leverage_analysis": "moderate",
                "overall_health": "good",
                "key_concerns": [
                    "Operating margin slightly below industry average"
                ],
                "key_strengths": [
                    "Strong liquidity position (current ratio > 2.0)",
                    "Conservative leverage (D/E < 0.5)"
                ],
                "classification_count": 3
            }
        }


class AnalysisResponse(BaseModel):
    """Complete analysis result response"""
    document_id: UUID = Field(
        ...,
        description="Document UUID that was analyzed"
    )
    analysis_type: str = Field(
        ...,
        description="Type of analysis performed"
    )
    quality_score: float = Field(
        ...,
        description="Quality score (0-100) based on data completeness and calculation success"
    )
    metrics: List[MetricResponse] = Field(
        default_factory=list,
        description="List of calculated financial metrics"
    )
    insights: InsightResponse = Field(
        ...,
        description="AI-generated insights and classifications"
    )
    cached: bool = Field(
        default=False,
        description="Whether result was retrieved from cache"
    )
    execution_time_ms: float = Field(
        ...,
        description="Total execution time in milliseconds"
    )
    timestamp: datetime = Field(
        ...,
        description="Analysis timestamp"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "550e8400-e29b-41d4-a716-446655440000",
                "analysis_type": "comprehensive",
                "quality_score": 87.5,
                "metrics": [
                    {
                        "metric_name": "current_ratio",
                        "metric_value": 2.15,
                        "metric_unit": "ratio",
                        "interpretation": "Strong liquidity",
                        "category": "liquidity",
                        "citations": []
                    }
                ],
                "insights": {
                    "risk_assessment": "low",
                    "liquidity_position": "strong",
                    "profitability_trends": "stable",
                    "leverage_analysis": "moderate",
                    "overall_health": "good",
                    "key_concerns": [],
                    "key_strengths": ["Strong liquidity position"],
                    "classification_count": 3
                },
                "cached": False,
                "execution_time_ms": 2543.75,
                "timestamp": "2025-11-10T15:30:00Z"
            }
        }


class SearchRequest(BaseModel):
    """Request model for semantic search"""
    case_id: Optional[UUID] = Field(
        None,
        description="Case UUID to search within (mutually exclusive with document_id)"
    )
    document_id: Optional[UUID] = Field(
        None,
        description="Document UUID to search within (mutually exclusive with case_id)"
    )
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Natural language search query"
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of results to return"
    )
    context_window: int = Field(
        default=1,
        ge=0,
        le=5,
        description="Number of surrounding chunks to include as context"
    )

    @validator('case_id')
    def validate_id_exclusivity(cls, v, values):
        """Ensure case_id and document_id are mutually exclusive"""
        if v is None and values.get('document_id') is None:
            raise ValueError("Either case_id or document_id must be provided")
        if v is not None and values.get('document_id') is not None:
            raise ValueError("case_id and document_id are mutually exclusive")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "case_id": "550e8400-e29b-41d4-a716-446655440000",
                "query": "What is the company's revenue growth?",
                "limit": 10,
                "context_window": 1
            }
        }


class SearchResultResponse(BaseModel):
    """Individual search result"""
    chunk_id: str = Field(
        ...,
        description="Unique chunk identifier"
    )
    document_id: UUID = Field(
        ...,
        description="Document UUID this chunk belongs to"
    )
    page_num: int = Field(
        ...,
        description="Page number in the document"
    )
    text: str = Field(
        ...,
        description="Chunk text content"
    )
    score: float = Field(
        ...,
        description="Relevance score (0-1)"
    )
    context: Optional[Dict[str, List[Dict]]] = Field(
        None,
        description="Surrounding chunks for context (before/after)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "chunk_id": "doc123_chunk_45",
                "document_id": "550e8400-e29b-41d4-a716-446655440000",
                "page_num": 5,
                "text": "Total revenue for FY2024 was $2.5M, representing 15% growth...",
                "score": 0.92,
                "context": {
                    "before": [{"text": "Previous context chunk"}],
                    "after": [{"text": "Next context chunk"}]
                }
            }
        }


class MetricsOnlyResponse(BaseModel):
    """Response containing only metrics"""
    document_id: UUID
    metrics: List[MetricResponse]
    total_count: int
    timestamp: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "550e8400-e29b-41d4-a716-446655440000",
                "metrics": [
                    {
                        "metric_name": "current_ratio",
                        "metric_value": 2.15,
                        "metric_unit": "ratio",
                        "interpretation": "Strong liquidity",
                        "category": "liquidity",
                        "citations": []
                    }
                ],
                "total_count": 1,
                "timestamp": "2025-11-10T15:30:00Z"
            }
        }


class InsightsOnlyResponse(BaseModel):
    """Response containing only insights"""
    document_id: UUID
    insights: InsightResponse
    timestamp: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "550e8400-e29b-41d4-a716-446655440000",
                "insights": {
                    "risk_assessment": "low",
                    "liquidity_position": "strong",
                    "profitability_trends": "stable",
                    "leverage_analysis": "moderate",
                    "overall_health": "good",
                    "key_concerns": [],
                    "key_strengths": ["Strong liquidity position"],
                    "classification_count": 3
                },
                "timestamp": "2025-11-10T15:30:00Z"
            }
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _convert_analysis_result_to_response(
    result: AnalysisResult,
    execution_time_ms: float
) -> AnalysisResponse:
    """
    Convert AnalysisResult dataclass to AnalysisResponse Pydantic model

    Args:
        result: AnalysisResult from AnalysisFlow
        execution_time_ms: Execution time in milliseconds

    Returns:
        AnalysisResponse Pydantic model
    """
    # Convert metrics to response format
    metrics_list = []

    # Process liquidity metrics
    for metric in result.metrics.liquidity_ratios:
        if metric.metric_value is not None:
            metrics_list.append(MetricResponse(
                metric_name=metric.metric_name,
                metric_value=metric.metric_value,
                metric_unit=metric.metric_unit,
                interpretation=metric.interpretation,
                category="liquidity",
                citations=[metric.citation_data] if metric.citation_data else []
            ))

    # Process profitability metrics
    for metric in result.metrics.profitability_ratios:
        if metric.metric_value is not None:
            metrics_list.append(MetricResponse(
                metric_name=metric.metric_name,
                metric_value=metric.metric_value,
                metric_unit=metric.metric_unit,
                interpretation=metric.interpretation,
                category="profitability",
                citations=[metric.citation_data] if metric.citation_data else []
            ))

    # Process leverage metrics
    for metric in result.metrics.leverage_ratios:
        if metric.metric_value is not None:
            metrics_list.append(MetricResponse(
                metric_name=metric.metric_name,
                metric_value=metric.metric_value,
                metric_unit=metric.metric_unit,
                interpretation=metric.interpretation,
                category="leverage",
                citations=[metric.citation_data] if metric.citation_data else []
            ))

    # Convert insights
    insights = InsightResponse(
        risk_assessment=result.insights.risk_assessment,
        liquidity_position=result.insights.liquidity_position,
        profitability_trends=result.insights.profitability_trends,
        leverage_analysis=result.insights.leverage_analysis,
        overall_health=result.insights.overall_health,
        key_concerns=result.insights.key_concerns,
        key_strengths=result.insights.key_strengths,
        classification_count=result.insights.classification_count
    )

    return AnalysisResponse(
        document_id=result.document_id,
        analysis_type=result.analysis_type,
        quality_score=result.quality_score,
        metrics=metrics_list,
        insights=insights,
        cached=result.cached,
        execution_time_ms=execution_time_ms,
        timestamp=result.timestamp
    )


def _convert_search_results(
    results: List[SearchResult]
) -> List[SearchResultResponse]:
    """
    Convert SearchResult dataclasses to SearchResultResponse Pydantic models

    Args:
        results: List of SearchResult from AnalysisFlow

    Returns:
        List of SearchResultResponse Pydantic models
    """
    return [
        SearchResultResponse(
            chunk_id=r.chunk_id,
            document_id=r.document_id,
            page_num=r.page_num,
            text=r.text,
            score=r.score,
            context=r.context
        )
        for r in results
    ]


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze financial document",
    description="""
    Perform comprehensive financial analysis on a document.

    Supported analysis types:
    - **comprehensive**: All 19 ratios + micro-agent insights (liquidity, profitability, leverage)
    - **liquidity**: 5 liquidity ratios only (current, quick, cash, operating CF, defensive interval)
    - **profitability**: 8 profitability ratios only (gross margin, operating margin, net margin, ROA, ROE, ROIC, EPS, asset turnover)
    - **leverage**: 6 leverage ratios only (debt-to-equity, debt-to-assets, interest coverage, debt service coverage, equity multiplier, financial leverage)
    - **quick**: Key ratios only (current ratio, ROE, debt-to-equity)

    Results are automatically cached for 1 hour. Subsequent requests return cached results instantly.
    """
)
async def analyze_document(request: AnalysisRequest) -> AnalysisResponse:
    """
    Run financial analysis on document

    Args:
        request: AnalysisRequest with document_id and analysis_type

    Returns:
        AnalysisResponse with metrics, insights, and metadata

    Raises:
        HTTPException 404: Document not found
        HTTPException 500: Analysis failed
    """
    if _analysis_flow is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analysis service not initialized"
        )

    logger.info(
        f"Analysis request: document={request.document_id}, "
        f"type={request.analysis_type}"
    )

    start_time = time.time()

    try:
        # Check if document exists
        if _postgres_store:
            document = _postgres_store.get_document(request.document_id)
            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document {request.document_id} not found"
                )

        # Perform analysis
        result = await _analysis_flow.analyze_document(
            document_id=request.document_id,
            analysis_type=request.analysis_type
        )

        execution_time = (time.time() - start_time) * 1000

        # Convert to response model
        response = _convert_analysis_result_to_response(result, execution_time)

        logger.info(
            f"Analysis complete: {len(response.metrics)} metrics, "
            f"quality={response.quality_score}%, cached={response.cached}, "
            f"time={execution_time:.0f}ms"
        )

        return response

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Invalid analysis request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get(
    "/{document_id}",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Get cached analysis results",
    description="""
    Retrieve cached analysis results for a document.

    This endpoint returns previously computed analysis results from cache.
    If no cached results exist, returns 404. Use POST /analyze to generate new results.
    """
)
async def get_cached_analysis(
    document_id: UUID = Path(
        ...,
        description="Document UUID to retrieve analysis for"
    ),
    analysis_type: str = Query(
        default="comprehensive",
        description="Type of analysis to retrieve"
    )
) -> AnalysisResponse:
    """
    Get cached analysis results

    Args:
        document_id: Document UUID
        analysis_type: Analysis type to retrieve

    Returns:
        AnalysisResponse with cached results

    Raises:
        HTTPException 404: No cached results found
    """
    if _analysis_flow is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analysis service not initialized"
        )

    logger.info(
        f"Cached analysis request: document={document_id}, "
        f"type={analysis_type}"
    )

    start_time = time.time()

    try:
        # Try to get from cache (analyze_document checks cache first)
        result = await _analysis_flow.analyze_document(
            document_id=document_id,
            analysis_type=analysis_type
        )

        execution_time = (time.time() - start_time) * 1000

        if not result.cached:
            # No cached result - this is a new computation
            # Return 404 to indicate no cached result exists
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No cached analysis found for document {document_id} "
                       f"with type {analysis_type}. Use POST /analyze to generate."
            )

        response = _convert_analysis_result_to_response(result, execution_time)

        logger.info(f"Cached analysis retrieved in {execution_time:.0f}ms")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve cached analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve analysis: {str(e)}"
        )


@router.post(
    "/search",
    response_model=List[SearchResultResponse],
    status_code=status.HTTP_200_OK,
    summary="Semantic search across case or document",
    description="""
    Perform semantic search across documents using natural language queries.

    Provide either case_id (search all documents in case) or document_id (search single document).
    Results are ranked by relevance with optional context windows.
    """
)
async def semantic_search(request: SearchRequest) -> List[SearchResultResponse]:
    """
    Semantic search across case or document

    Args:
        request: SearchRequest with query and scope

    Returns:
        List of SearchResultResponse with ranked results

    Raises:
        HTTPException 400: Invalid request
        HTTPException 404: Case/document not found
        HTTPException 500: Search failed
    """
    if _analysis_flow is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analysis service not initialized"
        )

    logger.info(
        f"Search request: query='{request.query[:50]}...', "
        f"case_id={request.case_id}, document_id={request.document_id}, "
        f"limit={request.limit}, context={request.context_window}"
    )

    try:
        if request.case_id:
            # Search across case
            results = await _analysis_flow.query_case(
                case_id=request.case_id,
                query=request.query,
                context_window=request.context_window
            )
        else:
            # Search single document
            # Note: AnalysisFlow doesn't have a direct document search method
            # We can use query_case with document filter if available
            # For now, return error suggesting to use case_id
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document-specific search not yet implemented. "
                       "Please use case_id to search across all case documents."
            )

        # Apply limit
        results = results[:request.limit]

        # Convert to response model
        response = _convert_search_results(results)

        logger.info(f"Search complete: {len(response)} results returned")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.get(
    "/{document_id}/metrics",
    response_model=MetricsOnlyResponse,
    status_code=status.HTTP_200_OK,
    summary="Get specific metrics for document",
    description="""
    Retrieve calculated financial metrics for a document.

    Returns all stored metrics from PostgreSQL. Optionally filter by metric names.
    """
)
async def get_document_metrics(
    document_id: UUID = Path(
        ...,
        description="Document UUID to retrieve metrics for"
    ),
    metric_names: Optional[str] = Query(
        None,
        description="Comma-separated list of metric names to filter (e.g., 'current_ratio,roe')"
    )
) -> MetricsOnlyResponse:
    """
    Get specific metrics for document

    Args:
        document_id: Document UUID
        metric_names: Optional comma-separated metric names

    Returns:
        MetricsOnlyResponse with requested metrics

    Raises:
        HTTPException 404: Document not found or no metrics available
    """
    if _postgres_store is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Storage service not initialized"
        )

    logger.info(
        f"Metrics request: document={document_id}, "
        f"filter={metric_names or 'all'}"
    )

    try:
        # Parse metric names if provided
        names_list = None
        if metric_names:
            names_list = [n.strip() for n in metric_names.split(',')]

        # Retrieve metrics from PostgreSQL
        stored_metrics = _postgres_store.get_metrics(
            document_id=document_id,
            metric_names=names_list
        )

        if not stored_metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No metrics found for document {document_id}"
            )

        # Convert to response format
        metrics_list = []
        for m in stored_metrics:
            # Determine category from metric name
            category = "unknown"
            if m['metric_name'] in ['current_ratio', 'quick_ratio', 'cash_ratio',
                                     'operating_cash_flow_ratio', 'defensive_interval_ratio']:
                category = "liquidity"
            elif m['metric_name'] in ['gross_margin', 'operating_margin', 'net_margin',
                                       'roa', 'roe', 'roic', 'eps', 'asset_turnover']:
                category = "profitability"
            elif m['metric_name'] in ['debt_to_equity', 'debt_to_assets',
                                       'interest_coverage', 'debt_service_coverage',
                                       'equity_multiplier', 'financial_leverage']:
                category = "leverage"

            metrics_list.append(MetricResponse(
                metric_name=m['metric_name'],
                metric_value=m.get('metric_value'),
                metric_unit=m.get('metric_unit'),
                interpretation="Stored metric value",
                category=category,
                citations=[{
                    'page_number': m.get('page_number'),
                    'calculation_method': m.get('calculation_method')
                }] if m.get('page_number') else []
            ))

        response = MetricsOnlyResponse(
            document_id=document_id,
            metrics=metrics_list,
            total_count=len(metrics_list),
            timestamp=datetime.now()
        )

        logger.info(f"Metrics retrieved: {len(metrics_list)} metrics returned")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve metrics: {str(e)}"
        )


@router.get(
    "/{document_id}/insights",
    response_model=InsightsOnlyResponse,
    status_code=status.HTTP_200_OK,
    summary="Get AI insights for document",
    description="""
    Retrieve AI-generated insights for a document.

    Runs micro-agent classifiers on stored metrics to generate:
    - Risk assessment
    - Liquidity position
    - Profitability trends
    - Leverage analysis
    - Overall health score
    - Key concerns and strengths
    """
)
async def get_document_insights(
    document_id: UUID = Path(
        ...,
        description="Document UUID to generate insights for"
    )
) -> InsightsOnlyResponse:
    """
    Get AI insights for document

    Args:
        document_id: Document UUID

    Returns:
        InsightsOnlyResponse with AI-generated insights

    Raises:
        HTTPException 404: Document not found or insufficient data
    """
    if _analysis_flow is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analysis service not initialized"
        )

    logger.info(f"Insights request: document={document_id}")

    try:
        # Generate insights from stored metrics
        insights = await _analysis_flow.generate_insights(
            document_id=document_id
        )

        # Check if we have sufficient data
        if insights.classification_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Insufficient data to generate insights for document {document_id}. "
                       "Please run analysis first using POST /analyze."
            )

        # Convert to response model
        response = InsightsOnlyResponse(
            document_id=document_id,
            insights=InsightResponse(
                risk_assessment=insights.risk_assessment,
                liquidity_position=insights.liquidity_position,
                profitability_trends=insights.profitability_trends,
                leverage_analysis=insights.leverage_analysis,
                overall_health=insights.overall_health,
                key_concerns=insights.key_concerns,
                key_strengths=insights.key_strengths,
                classification_count=insights.classification_count
            ),
            timestamp=datetime.now()
        )

        logger.info(
            f"Insights generated: {insights.classification_count} classifications, "
            f"health={insights.overall_health}"
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate insights: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate insights: {str(e)}"
        )


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check if the analysis API is operational"
)
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint

    Returns:
        Dict with service status
    """
    return {
        "status": "healthy",
        "service": "analysis_api",
        "initialized": _analysis_flow is not None,
        "timestamp": datetime.now().isoformat()
    }
