"""
Shared Pydantic Models for FastAPI Routes
Provides base models, error responses, pagination, and status enums
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any, Dict, Generic, TypeVar
from datetime import datetime
from uuid import UUID
from enum import Enum


# ============================================================================
# STATUS ENUMS
# ============================================================================

class DocumentStatus(str, Enum):
    """Document processing status"""
    PENDING = "pending"
    VALIDATING = "validating"
    EXTRACTING = "extracting"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    STORING = "storing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisStatus(str, Enum):
    """Analysis workflow status"""
    QUEUED = "queued"
    SEARCHING = "searching"
    CALCULATING = "calculating"
    CLASSIFYING = "classifying"
    COMPLETED = "completed"
    FAILED = "failed"


class CaseStatus(str, Enum):
    """Case status"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    UNDER_REVIEW = "under_review"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    CLOSED = "closed"


# ============================================================================
# BASE MODELS
# ============================================================================

class TimestampedModel(BaseModel):
    """Base model with timestamp fields"""
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when the record was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when the record was last updated"
    )

    model_config = ConfigDict(from_attributes=True)


class IdentifiedModel(TimestampedModel):
    """Base model with ID and timestamps"""
    id: UUID = Field(
        description="Unique identifier for the record"
    )


# ============================================================================
# ERROR RESPONSE MODELS
# ============================================================================

class ErrorDetail(BaseModel):
    """Single error detail"""
    field: Optional[str] = Field(
        None,
        description="Field name that caused the error (for validation errors)"
    )
    message: str = Field(
        description="Error message"
    )
    error_type: Optional[str] = Field(
        None,
        description="Type of error (e.g., 'validation_error', 'not_found')"
    )


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(
        description="Error message"
    )
    detail: Optional[str] = Field(
        None,
        description="Additional error details"
    )
    error_code: Optional[str] = Field(
        None,
        description="Machine-readable error code"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When the error occurred"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "Document not found",
                "detail": "No document exists with ID: 123e4567-e89b-12d3-a456-426614174000",
                "error_code": "DOCUMENT_NOT_FOUND",
                "timestamp": "2025-11-10T12:34:56.789Z"
            }
        }
    )


class ValidationErrorDetail(BaseModel):
    """Validation error detail"""
    loc: List[str] = Field(
        description="Location of the validation error (e.g., ['body', 'email'])"
    )
    msg: str = Field(
        description="Error message"
    )
    type: str = Field(
        description="Error type (e.g., 'value_error', 'type_error')"
    )


class ValidationErrorResponse(BaseModel):
    """Validation error response with field-level details"""
    error: str = Field(
        default="Validation error",
        description="Error type"
    )
    errors: List[ValidationErrorDetail] = Field(
        description="List of validation errors"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When the error occurred"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "Validation error",
                "errors": [
                    {
                        "loc": ["body", "email"],
                        "msg": "value is not a valid email address",
                        "type": "value_error.email"
                    }
                ],
                "timestamp": "2025-11-10T12:34:56.789Z"
            }
        }
    )


# ============================================================================
# PAGINATION MODELS
# ============================================================================

class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints"""
    page: int = Field(
        default=1,
        ge=1,
        description="Page number (starting from 1)"
    )
    page_size: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Number of items per page (max 100)"
    )

    @property
    def offset(self) -> int:
        """Calculate offset from page and page_size"""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Return limit (alias for page_size)"""
        return self.page_size


T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper"""
    items: List[T] = Field(
        description="List of items for current page"
    )
    total: int = Field(
        description="Total number of items across all pages"
    )
    page: int = Field(
        description="Current page number"
    )
    page_size: int = Field(
        description="Number of items per page"
    )
    total_pages: int = Field(
        description="Total number of pages"
    )
    has_next: bool = Field(
        description="Whether there is a next page"
    )
    has_prev: bool = Field(
        description="Whether there is a previous page"
    )

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        page_size: int
    ) -> "PaginatedResponse[T]":
        """
        Factory method to create paginated response

        Args:
            items: List of items for current page
            total: Total number of items
            page: Current page number
            page_size: Items per page

        Returns:
            PaginatedResponse with calculated fields
        """
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )


# ============================================================================
# SUCCESS RESPONSE MODELS
# ============================================================================

class MessageResponse(BaseModel):
    """Simple message response"""
    message: str = Field(
        description="Success or informational message"
    )
    detail: Optional[str] = Field(
        None,
        description="Additional details"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When the response was generated"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Document processing started",
                "detail": "Document queued for processing. Check status at /api/v1/documents/{document_id}/status",
                "timestamp": "2025-11-10T12:34:56.789Z"
            }
        }
    )


class StatusResponse(BaseModel):
    """Status check response"""
    status: str = Field(
        description="Current status"
    )
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional status details"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When the status was checked"
    )


# ============================================================================
# DOMAIN-SPECIFIC MODELS
# ============================================================================

class DocumentMetadata(BaseModel):
    """Document metadata for creation/update"""
    original_filename: str = Field(
        description="Original filename from upload"
    )
    document_type: str = Field(
        default="financial",
        description="Type of document (financial, legal, etc.)"
    )
    mime_type: str = Field(
        default="application/pdf",
        description="MIME type of the document"
    )
    file_size: int = Field(
        gt=0,
        description="File size in bytes"
    )
    pages_count: Optional[int] = Field(
        None,
        description="Number of pages in the document"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional custom metadata"
    )


class DocumentResponse(IdentifiedModel):
    """Document response model"""
    case_id: UUID = Field(
        description="Case this document belongs to"
    )
    filename: str = Field(
        description="Stored filename (unique)"
    )
    original_filename: str = Field(
        description="Original filename from upload"
    )
    document_type: str = Field(
        description="Type of document"
    )
    status: DocumentStatus = Field(
        description="Current processing status"
    )
    file_size: int = Field(
        description="File size in bytes"
    )
    pages_count: Optional[int] = Field(
        None,
        description="Number of pages"
    )
    processing_started_at: Optional[datetime] = Field(
        None,
        description="When processing started"
    )
    processing_completed_at: Optional[datetime] = Field(
        None,
        description="When processing completed"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional metadata"
    )


class CaseResponse(IdentifiedModel):
    """Case response model"""
    name: str = Field(
        description="Case name"
    )
    description: Optional[str] = Field(
        None,
        description="Case description"
    )
    status: CaseStatus = Field(
        description="Current case status"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional case metadata"
    )
    document_count: Optional[int] = Field(
        None,
        description="Number of documents in the case"
    )


class FinancialMetricResponse(BaseModel):
    """Financial metric response"""
    metric_name: str = Field(
        description="Name of the metric (e.g., 'current_ratio', 'roe')"
    )
    metric_value: Optional[float] = Field(
        None,
        description="Calculated metric value"
    )
    metric_unit: Optional[str] = Field(
        None,
        description="Unit of measurement (e.g., 'ratio', 'percent', 'currency')"
    )
    interpretation: Optional[str] = Field(
        None,
        description="Human-readable interpretation of the metric"
    )
    fiscal_year: Optional[int] = Field(
        None,
        description="Fiscal year for the metric"
    )
    fiscal_period: Optional[str] = Field(
        None,
        description="Fiscal period (Q1, Q2, Q3, Q4, Annual)"
    )
    confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Confidence score for the metric (0.0 to 1.0)"
    )
    page_number: Optional[int] = Field(
        None,
        description="Page number where data was found"
    )


class AnalysisResultResponse(BaseModel):
    """Analysis result response"""
    document_id: UUID = Field(
        description="Document that was analyzed"
    )
    analysis_type: str = Field(
        description="Type of analysis performed (comprehensive, liquidity, etc.)"
    )
    status: AnalysisStatus = Field(
        description="Analysis status"
    )
    quality_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Quality score of the analysis (0-100)"
    )
    metrics_calculated: Optional[int] = Field(
        None,
        description="Number of metrics successfully calculated"
    )
    insights: Optional[Dict[str, Any]] = Field(
        None,
        description="Analysis insights and classifications"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When the analysis was created"
    )
    cached: bool = Field(
        default=False,
        description="Whether this result was served from cache"
    )


class SearchResultResponse(BaseModel):
    """Semantic search result"""
    chunk_id: str = Field(
        description="Unique chunk identifier"
    )
    document_id: UUID = Field(
        description="Document containing the chunk"
    )
    case_id: UUID = Field(
        description="Case containing the document"
    )
    page_num: int = Field(
        description="Page number where the chunk is located"
    )
    text: str = Field(
        description="Chunk text content"
    )
    score: float = Field(
        ge=0.0,
        le=1.0,
        description="Relevance score (0.0 to 1.0)"
    )
    char_count: int = Field(
        description="Number of characters in the chunk"
    )
    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Surrounding context chunks (before and after)"
    )


# ============================================================================
# REQUEST MODELS
# ============================================================================

class CaseCreateRequest(BaseModel):
    """Request to create a new case"""
    name: str = Field(
        min_length=1,
        max_length=255,
        description="Case name"
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Case description"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional case metadata"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Company X Financial Investigation",
                "description": "Analysis of Company X financial documents for Q3 2024",
                "metadata": {
                    "client": "Law Firm ABC",
                    "priority": "high"
                }
            }
        }
    )


class CaseUpdateRequest(BaseModel):
    """Request to update an existing case"""
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Updated case name"
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Updated case description"
    )
    status: Optional[CaseStatus] = Field(
        None,
        description="Updated case status"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Updated metadata"
    )


class DocumentUploadResponse(BaseModel):
    """Response after document upload"""
    document_id: UUID = Field(
        description="Unique identifier for the uploaded document"
    )
    filename: str = Field(
        description="Stored filename"
    )
    original_filename: str = Field(
        description="Original filename from upload"
    )
    status: DocumentStatus = Field(
        description="Initial processing status"
    )
    message: str = Field(
        description="Success message"
    )
    processing_url: str = Field(
        description="URL to check processing status"
    )


class AnalysisRequest(BaseModel):
    """Request to start document analysis"""
    analysis_type: str = Field(
        default="comprehensive",
        description="Type of analysis to perform"
    )
    options: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional analysis options"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "analysis_type": "comprehensive",
                "options": {
                    "include_micro_agents": True,
                    "cache_results": True
                }
            }
        }
    )


class SearchRequest(BaseModel):
    """Request for semantic search"""
    query: str = Field(
        min_length=3,
        max_length=1000,
        description="Search query"
    )
    case_id: Optional[UUID] = Field(
        None,
        description="Limit search to specific case"
    )
    document_id: Optional[UUID] = Field(
        None,
        description="Limit search to specific document"
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of results"
    )
    score_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum relevance score"
    )
    context_window: int = Field(
        default=1,
        ge=0,
        le=5,
        description="Number of surrounding chunks to include"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "What is the company's revenue for Q3 2024?",
                "case_id": "123e4567-e89b-12d3-a456-426614174000",
                "limit": 10,
                "score_threshold": 0.7,
                "context_window": 1
            }
        }
    )


# ============================================================================
# HEALTH CHECK MODELS
# ============================================================================

class ComponentHealth(BaseModel):
    """Health status of a system component"""
    status: str = Field(
        description="Component status (healthy, degraded, unhealthy)"
    )
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional component details"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if unhealthy"
    )


class HealthCheckResponse(BaseModel):
    """System health check response"""
    status: str = Field(
        description="Overall system status"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When health check was performed"
    )
    components: Dict[str, ComponentHealth] = Field(
        description="Health status of individual components"
    )
    version: str = Field(
        description="API version"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "timestamp": "2025-11-10T12:34:56.789Z",
                "components": {
                    "postgres": {
                        "status": "healthy",
                        "details": {"host": "localhost", "database": "investigation_db"}
                    },
                    "redis": {
                        "status": "healthy",
                        "details": {"host": "localhost", "port": 6379}
                    },
                    "qdrant": {
                        "status": "healthy",
                        "details": {"collections_count": 1}
                    }
                },
                "version": "1.0.0"
            }
        }
    )
