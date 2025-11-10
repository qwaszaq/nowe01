"""
Case Management REST API Endpoints
Provides CRUD operations for investigation cases with pagination, filtering, and statistics
"""

import logging
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator

from src.storage.postgres_store import PostgresStore
from src.orchestration.state_manager import StateManager

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/cases", tags=["cases"])

# Initialize storage (in production, use dependency injection)
postgres_store = PostgresStore()
state_manager = StateManager(postgres_store=postgres_store)


# =========================================================================
# PYDANTIC MODELS
# =========================================================================

class CaseCreate(BaseModel):
    """Request model for creating a new case"""
    name: str = Field(..., min_length=1, max_length=255, description="Case name")
    description: Optional[str] = Field(None, max_length=2000, description="Case description")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate case name is not empty or whitespace only"""
        if not v or not v.strip():
            raise ValueError("Case name cannot be empty or whitespace")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Financial Fraud Investigation 2024-Q1",
                "description": "Investigation into suspected financial irregularities in Q1 2024 reports"
            }
        }


class CaseUpdate(BaseModel):
    """Request model for updating an existing case"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Case name")
    description: Optional[str] = Field(None, max_length=2000, description="Case description")
    status: Optional[str] = Field(None, description="Case status (active, completed, archived)")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate case name if provided"""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Case name cannot be empty or whitespace")
        return v.strip() if v else None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate status is one of allowed values"""
        if v is not None:
            allowed_statuses = ["active", "completed", "archived"]
            if v.lower() not in allowed_statuses:
                raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
            return v.lower()
        return None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Financial Fraud Investigation 2024-Q1 (Updated)",
                "description": "Updated description with new findings",
                "status": "active"
            }
        }


class CaseResponse(BaseModel):
    """Response model for a single case"""
    id: UUID = Field(..., description="Case unique identifier")
    name: str = Field(..., description="Case name")
    description: Optional[str] = Field(None, description="Case description")
    status: str = Field(..., description="Case status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    document_count: int = Field(default=0, description="Number of documents in this case")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Financial Fraud Investigation 2024-Q1",
                "description": "Investigation into suspected financial irregularities",
                "status": "active",
                "created_at": "2024-11-10T10:30:00",
                "updated_at": "2024-11-10T15:45:00",
                "document_count": 15
            }
        }


class CaseListResponse(BaseModel):
    """Response model for paginated list of cases"""
    cases: List[CaseResponse] = Field(..., description="List of cases")
    total: int = Field(..., description="Total number of cases matching filters")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")

    class Config:
        json_schema_extra = {
            "example": {
                "cases": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "Investigation A",
                        "description": "Description A",
                        "status": "active",
                        "created_at": "2024-11-10T10:30:00",
                        "updated_at": "2024-11-10T15:45:00",
                        "document_count": 15
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 20,
                "total_pages": 1
            }
        }


class CaseStats(BaseModel):
    """Response model for case processing statistics"""
    case_id: UUID = Field(..., description="Case unique identifier")
    total_documents: int = Field(..., description="Total documents in case")
    pending: int = Field(..., description="Documents pending processing")
    extracting: int = Field(..., description="Documents in extraction phase")
    chunking: int = Field(..., description="Documents being chunked")
    embedding: int = Field(..., description="Documents being embedded")
    storing: int = Field(..., description="Documents being stored")
    completed: int = Field(..., description="Successfully processed documents")
    failed: int = Field(..., description="Failed documents")
    success_rate: float = Field(..., description="Success rate percentage")
    error_rate: float = Field(..., description="Error rate percentage")
    avg_processing_time_seconds: Optional[float] = Field(None, description="Average processing time in seconds")
    errors_by_type: dict = Field(default_factory=dict, description="Error counts by type")

    class Config:
        json_schema_extra = {
            "example": {
                "case_id": "550e8400-e29b-41d4-a716-446655440000",
                "total_documents": 20,
                "pending": 2,
                "extracting": 1,
                "chunking": 0,
                "embedding": 0,
                "storing": 0,
                "completed": 15,
                "failed": 2,
                "success_rate": 75.0,
                "error_rate": 10.0,
                "avg_processing_time_seconds": 45.3,
                "errors_by_type": {
                    "extraction_error": 1,
                    "timeout_error": 1
                }
            }
        }


# =========================================================================
# HELPER FUNCTIONS
# =========================================================================

def _get_document_count(case_id: UUID) -> int:
    """
    Get document count for a case

    Args:
        case_id: Case identifier

    Returns:
        Number of documents in the case
    """
    try:
        documents = postgres_store.list_documents(case_id)
        return len(documents)
    except Exception as e:
        logger.error(f"Failed to get document count for case {case_id}: {e}")
        return 0


def _get_total_case_count(status_filter: Optional[str] = None) -> int:
    """
    Get total count of cases matching filter

    Args:
        status_filter: Optional status to filter by

    Returns:
        Total count of matching cases
    """
    try:
        with postgres_store.get_cursor() as cursor:
            if status_filter:
                cursor.execute(
                    "SELECT COUNT(*) as total FROM cases WHERE status = %s",
                    (status_filter,)
                )
            else:
                cursor.execute("SELECT COUNT(*) as total FROM cases")

            result = cursor.fetchone()
            return result['total'] if result else 0
    except Exception as e:
        logger.error(f"Failed to get total case count: {e}")
        return 0


def _build_case_response(case_data: dict) -> CaseResponse:
    """
    Build CaseResponse from database record

    Args:
        case_data: Database record as dict

    Returns:
        CaseResponse model
    """
    return CaseResponse(
        id=case_data['id'],
        name=case_data['name'],
        description=case_data.get('description'),
        status=case_data.get('status', 'active'),
        created_at=case_data['created_at'],
        updated_at=case_data['updated_at'],
        document_count=_get_document_count(case_data['id'])
    )


# =========================================================================
# API ENDPOINTS
# =========================================================================

@router.post(
    "/",
    response_model=CaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new case",
    description="Create a new investigation case with name and optional description"
)
async def create_case(case_data: CaseCreate) -> CaseResponse:
    """
    Create a new investigation case

    Args:
        case_data: Case creation data

    Returns:
        Created case details

    Raises:
        HTTPException: If case creation fails
    """
    try:
        logger.info(f"Creating new case: {case_data.name}")

        # Create case in database
        case_id = postgres_store.create_case(
            name=case_data.name,
            description=case_data.description
        )

        # Retrieve created case
        case_record = postgres_store.get_case(case_id)

        if not case_record:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Case created but could not be retrieved"
            )

        logger.info(f"Case created successfully: {case_id}")
        return _build_case_response(case_record)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create case: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create case: {str(e)}"
        )


@router.get(
    "/",
    response_model=CaseListResponse,
    summary="List all cases",
    description="Retrieve paginated list of cases with optional status filtering"
)
async def list_cases(
    status: Optional[str] = Query(None, description="Filter by status (active, completed, archived)"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page")
) -> CaseListResponse:
    """
    List all cases with pagination and optional filtering

    Args:
        status: Optional status filter
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        Paginated list of cases

    Raises:
        HTTPException: If listing fails
    """
    try:
        # Validate status if provided
        if status:
            allowed_statuses = ["active", "completed", "archived"]
            if status.lower() not in allowed_statuses:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status. Must be one of: {', '.join(allowed_statuses)}"
                )
            status = status.lower()

        # Calculate offset
        offset = (page - 1) * page_size

        # Get total count
        total_count = _get_total_case_count(status)

        # Calculate total pages
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0

        # Retrieve cases
        cases = postgres_store.list_cases(
            status=status,
            limit=page_size,
            offset=offset
        )

        # Build response models
        case_responses = [_build_case_response(case) for case in cases]

        logger.info(f"Retrieved {len(case_responses)} cases (page {page}/{total_pages})")

        return CaseListResponse(
            cases=case_responses,
            total=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list cases: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve cases: {str(e)}"
        )


@router.get(
    "/{case_id}",
    response_model=CaseResponse,
    summary="Get case details",
    description="Retrieve detailed information about a specific case including document count"
)
async def get_case(case_id: UUID) -> CaseResponse:
    """
    Get detailed information about a specific case

    Args:
        case_id: Case unique identifier

    Returns:
        Case details with document count

    Raises:
        HTTPException: If case not found or retrieval fails
    """
    try:
        logger.info(f"Retrieving case: {case_id}")

        # Retrieve case from database
        case_record = postgres_store.get_case(case_id)

        if not case_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case not found: {case_id}"
            )

        return _build_case_response(case_record)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get case {case_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve case: {str(e)}"
        )


@router.patch(
    "/{case_id}",
    response_model=CaseResponse,
    summary="Update case",
    description="Update case name, description, or status"
)
async def update_case(case_id: UUID, case_update: CaseUpdate) -> CaseResponse:
    """
    Update an existing case

    Args:
        case_id: Case unique identifier
        case_update: Fields to update

    Returns:
        Updated case details

    Raises:
        HTTPException: If case not found or update fails
    """
    try:
        logger.info(f"Updating case: {case_id}")

        # Check if case exists
        existing_case = postgres_store.get_case(case_id)
        if not existing_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case not found: {case_id}"
            )

        # Build update dict (only include fields that were provided)
        update_fields = {}
        if case_update.name is not None:
            update_fields['name'] = case_update.name
        if case_update.description is not None:
            update_fields['description'] = case_update.description
        if case_update.status is not None:
            update_fields['status'] = case_update.status

        # Check if any fields to update
        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided for update"
            )

        # Update case
        success = postgres_store.update_case(case_id, **update_fields)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update case"
            )

        # Retrieve updated case
        updated_case = postgres_store.get_case(case_id)

        logger.info(f"Case updated successfully: {case_id}")
        return _build_case_response(updated_case)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update case {case_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update case: {str(e)}"
        )


@router.delete(
    "/{case_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete case",
    description="Soft delete a case by setting status to 'archived'"
)
async def delete_case(case_id: UUID) -> dict:
    """
    Soft delete a case (sets status to archived)

    Args:
        case_id: Case unique identifier

    Returns:
        Success message

    Raises:
        HTTPException: If case not found or deletion fails
    """
    try:
        logger.info(f"Deleting (archiving) case: {case_id}")

        # Check if case exists
        existing_case = postgres_store.get_case(case_id)
        if not existing_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case not found: {case_id}"
            )

        # Soft delete by setting status to archived
        success = postgres_store.update_case(case_id, status='archived')

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to archive case"
            )

        logger.info(f"Case archived successfully: {case_id}")

        return {
            "message": f"Case {case_id} archived successfully",
            "case_id": str(case_id),
            "status": "archived"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete case {case_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to archive case: {str(e)}"
        )


@router.get(
    "/{case_id}/stats",
    response_model=CaseStats,
    summary="Get case statistics",
    description="Retrieve processing statistics for a specific case including document states and error rates"
)
async def get_case_stats(case_id: UUID) -> CaseStats:
    """
    Get processing statistics for a case

    Args:
        case_id: Case unique identifier

    Returns:
        Processing statistics including document states and error rates

    Raises:
        HTTPException: If case not found or stats retrieval fails
    """
    try:
        logger.info(f"Retrieving statistics for case: {case_id}")

        # Check if case exists
        existing_case = postgres_store.get_case(case_id)
        if not existing_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case not found: {case_id}"
            )

        # Get processing statistics from state manager
        stats = state_manager.get_processing_stats(case_id=case_id)

        # Build response
        return CaseStats(
            case_id=case_id,
            total_documents=stats.total_documents,
            pending=stats.pending,
            extracting=stats.extracting,
            chunking=stats.chunking,
            embedding=stats.embedding,
            storing=stats.storing,
            completed=stats.completed,
            failed=stats.failed,
            success_rate=stats.success_rate,
            error_rate=stats.error_rate,
            avg_processing_time_seconds=stats.avg_processing_time_seconds,
            errors_by_type=stats.errors_by_type
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get stats for case {case_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve case statistics: {str(e)}"
        )
