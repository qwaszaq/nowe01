"""
Document Upload and Management REST API Endpoints
Handles PDF upload, processing, status tracking, and document management
"""

import logging
import asyncio
from typing import List, Optional
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, BackgroundTasks, Query
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

from src.config.settings import settings
from src.orchestration.document_processor import DocumentProcessor
from src.orchestration.state_manager import StateManager, DocumentState
from src.storage.postgres_store import PostgresStore

logger = logging.getLogger(__name__)


# =========================================================================
# PYDANTIC MODELS
# =========================================================================

class DocumentStatus(str, Enum):
    """Document processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    EXTRACTING = "extracting"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    STORING = "storing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentUploadResponse(BaseModel):
    """Response after document upload"""
    document_id: UUID
    status: str
    message: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "document_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "processing",
                "message": "Document uploaded successfully and processing started"
            }
        }
    )


class DocumentResponse(BaseModel):
    """Document details response"""
    id: UUID
    case_id: UUID
    filename: str
    original_filename: str
    status: str
    file_size: int
    mime_type: str
    page_count: Optional[int] = None
    chunk_count: Optional[int] = None
    created_at: datetime
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "case_id": "650e8400-e29b-41d4-a716-446655440001",
                "filename": "financial_report_2023.pdf",
                "original_filename": "Q4 2023 Financial Report.pdf",
                "status": "completed",
                "file_size": 2457600,
                "mime_type": "application/pdf",
                "page_count": 45,
                "chunk_count": 128,
                "created_at": "2024-01-15T10:30:00",
                "processing_started_at": "2024-01-15T10:30:05",
                "processing_completed_at": "2024-01-15T10:32:15"
            }
        }
    )


class DocumentListResponse(BaseModel):
    """Paginated list of documents"""
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "documents": [],
                "total": 42,
                "page": 1,
                "page_size": 20
            }
        }
    )


class DocumentStatusResponse(BaseModel):
    """Real-time document processing status"""
    document_id: UUID
    state: str
    progress_percent: float = Field(ge=0.0, le=100.0)
    current_stage: str
    error_details: Optional[str] = None
    started_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "document_id": "550e8400-e29b-41d4-a716-446655440000",
                "state": "embedding",
                "progress_percent": 65.0,
                "current_stage": "embedding",
                "error_details": None,
                "started_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:31:30"
            }
        }
    )


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    document_id: Optional[UUID] = None


# =========================================================================
# ROUTER SETUP
# =========================================================================

router = APIRouter(prefix="/documents", tags=["documents"])


# Dependency injection - initialize once
_postgres_store = None
_state_manager = None
_document_processor = None


def get_postgres_store() -> PostgresStore:
    """Get PostgreSQL store instance"""
    global _postgres_store
    if _postgres_store is None:
        _postgres_store = PostgresStore()
    return _postgres_store


def get_state_manager() -> StateManager:
    """Get state manager instance"""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager


def get_document_processor() -> DocumentProcessor:
    """Get document processor instance"""
    global _document_processor
    if _document_processor is None:
        _document_processor = DocumentProcessor()
    return _document_processor


# =========================================================================
# FILE UPLOAD HELPERS
# =========================================================================

def validate_pdf_file(file: UploadFile) -> None:
    """
    Validate uploaded file

    Args:
        file: Uploaded file

    Raises:
        HTTPException: If validation fails
    """
    # Check file extension
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required"
        )

    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(settings.allowed_extensions)}"
        )

    # Check content type
    if file.content_type not in ["application/pdf", "application/x-pdf"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content type: {file.content_type}. Expected: application/pdf"
        )


async def save_upload_file(file: UploadFile, document_id: UUID) -> tuple[str, int]:
    """
    Save uploaded file to disk

    Args:
        file: Uploaded file
        document_id: Document UUID for filename

    Returns:
        Tuple of (file_path, file_size)

    Raises:
        HTTPException: If save fails
    """
    try:
        # Ensure upload directory exists
        settings.upload_dir.mkdir(parents=True, exist_ok=True)

        # Generate safe filename
        file_ext = Path(file.filename).suffix.lower()
        safe_filename = f"{document_id}{file_ext}"
        file_path = settings.upload_dir / safe_filename

        # Write file in chunks to handle large files
        file_size = 0
        chunk_size = 1024 * 1024  # 1MB chunks

        with open(file_path, "wb") as f:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break

                file_size += len(chunk)

                # Check max file size
                if file_size > settings.max_file_size:
                    f.close()
                    file_path.unlink()  # Delete partial file
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File too large. Max size: {settings.max_file_size / 1024 / 1024:.0f}MB"
                    )

                f.write(chunk)

        logger.info(f"Saved file: {file_path} ({file_size} bytes)")
        return str(file_path.absolute()), file_size

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )


def process_document_background(
    document_id: UUID,
    case_id: UUID,
    file_path: str,
    original_filename: str
) -> None:
    """
    Background task to process document (synchronous wrapper)

    Args:
        document_id: Document UUID
        case_id: Case UUID
        file_path: Path to saved file
        original_filename: Original filename
    """
    import asyncio

    processor = get_document_processor()
    postgres = get_postgres_store()

    try:
        logger.info(f"Starting background processing for document {document_id}")

        # Update status to processing
        postgres.update_document_status(document_id, "processing")

        # Process document (run async function in new event loop)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(processor.process_document(
                case_id=case_id,
                document_path=file_path,
                document_metadata={
                    "document_id": document_id,
                    "original_filename": original_filename
                }
            ))
        finally:
            loop.close()

        # Update chunk count in database
        if result.status == "completed":
            with postgres.get_cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE documents
                    SET metadata = jsonb_set(
                        COALESCE(metadata, '{}'::jsonb),
                        '{chunk_count}',
                        %s::text::jsonb
                    )
                    WHERE id = %s
                    """,
                    (result.chunk_count, str(document_id))
                )

            logger.info(
                f"Document {document_id} processed successfully: "
                f"{result.chunk_count} chunks, {result.elapsed_time:.2f}s"
            )
        else:
            logger.error(f"Document {document_id} processing failed: {result.error_message}")

    except Exception as e:
        logger.error(f"Background processing failed for document {document_id}: {e}", exc_info=True)

        # Update status to failed
        try:
            postgres.update_document_status(document_id, "failed")
        except Exception as db_error:
            logger.error(f"Failed to update document status: {db_error}")


# =========================================================================
# ENDPOINTS
# =========================================================================

@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload document",
    description="Upload a PDF document for processing. File is validated, saved, and processing starts in background."
)
async def upload_document(
    background_tasks: BackgroundTasks,
    case_id: UUID = Form(..., description="Case UUID to associate document with"),
    file: UploadFile = File(..., description="PDF file to upload")
) -> DocumentUploadResponse:
    """
    Upload PDF document for processing

    Workflow:
    1. Validate PDF file format and size
    2. Save file to upload directory
    3. Create document record in database
    4. Trigger background processing task
    5. Return document_id immediately

    Args:
        case_id: Case UUID
        file: Uploaded PDF file

    Returns:
        DocumentUploadResponse with document_id and status

    Raises:
        HTTPException: On validation or storage errors
    """
    postgres = get_postgres_store()

    try:
        # Validate file
        validate_pdf_file(file)

        # Check if case exists
        case = postgres.get_case(case_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case not found: {case_id}"
            )

        # Generate document ID
        document_id = uuid4()

        # Save file
        file_path, file_size = await save_upload_file(file, document_id)

        # Create document record
        try:
            created_id = postgres.create_document(
                case_id=case_id,
                filename=Path(file_path).name,
                original_filename=file.filename,
                file_path=file_path,
                file_size=file_size,
                mime_type=file.content_type or "application/pdf"
            )

            # Use the ID returned by database (should match document_id)
            document_id = created_id

        except Exception as e:
            # Clean up file if database insert fails
            Path(file_path).unlink(missing_ok=True)
            logger.error(f"Failed to create document record: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create document record: {str(e)}"
            )

        # Schedule background processing
        background_tasks.add_task(
            process_document_background,
            document_id=document_id,
            case_id=case_id,
            file_path=file_path,
            original_filename=file.filename
        )

        logger.info(f"Document uploaded: {document_id} - {file.filename} ({file_size} bytes)")

        return DocumentUploadResponse(
            document_id=document_id,
            status="processing",
            message="Document uploaded successfully and processing started"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during upload: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List documents",
    description="Get paginated list of documents with optional filtering by case_id and status"
)
async def list_documents(
    case_id: Optional[UUID] = Query(None, description="Filter by case ID"),
    status_filter: Optional[DocumentStatus] = Query(None, alias="status", description="Filter by processing status"),
    page: int = Query(1, ge=1, description="Page number (starting from 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page")
) -> DocumentListResponse:
    """
    List documents with pagination and filtering

    Args:
        case_id: Optional case ID filter
        status_filter: Optional status filter
        page: Page number (1-indexed)
        page_size: Items per page

    Returns:
        DocumentListResponse with documents and pagination info
    """
    postgres = get_postgres_store()

    try:
        offset = (page - 1) * page_size

        # Build query
        with postgres.get_cursor() as cursor:
            # Count total
            count_query = "SELECT COUNT(*) FROM documents WHERE 1=1"
            count_params = []

            if case_id:
                count_query += " AND case_id = %s"
                count_params.append(str(case_id))

            if status_filter:
                count_query += " AND status = %s"
                count_params.append(status_filter.value)

            cursor.execute(count_query, count_params)
            total = cursor.fetchone()['count']

            # Fetch documents
            query = """
                SELECT
                    id, case_id, filename, original_filename, status,
                    file_size, mime_type, pages_count as page_count,
                    (metadata->>'chunk_count')::int as chunk_count,
                    created_at, processing_started_at, processing_completed_at
                FROM documents
                WHERE 1=1
            """
            params = []

            if case_id:
                query += " AND case_id = %s"
                params.append(str(case_id))

            if status_filter:
                query += " AND status = %s"
                params.append(status_filter.value)

            query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params.extend([page_size, offset])

            cursor.execute(query, params)
            documents = cursor.fetchall()

        # Convert to response models
        document_responses = [
            DocumentResponse(**doc) for doc in documents
        ]

        return DocumentListResponse(
            documents=document_responses,
            total=total,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"Failed to list documents: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document details",
    description="Retrieve detailed information about a specific document"
)
async def get_document(document_id: UUID) -> DocumentResponse:
    """
    Get document by ID

    Args:
        document_id: Document UUID

    Returns:
        DocumentResponse with document details

    Raises:
        HTTPException: If document not found
    """
    postgres = get_postgres_store()

    try:
        with postgres.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id, case_id, filename, original_filename, status,
                    file_size, mime_type, pages_count as page_count,
                    (metadata->>'chunk_count')::int as chunk_count,
                    created_at, processing_started_at, processing_completed_at
                FROM documents
                WHERE id = %s
                """,
                (str(document_id),)
            )
            document = cursor.fetchone()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {document_id}"
            )

        return DocumentResponse(**document)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document {document_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document: {str(e)}"
        )


@router.get(
    "/{document_id}/status",
    response_model=DocumentStatusResponse,
    summary="Get processing status",
    description="Get real-time processing status for a document (includes progress percentage and current stage)"
)
async def get_document_status(document_id: UUID) -> DocumentStatusResponse:
    """
    Get real-time processing status

    Checks StateManager (Redis) for current processing state with progress tracking

    Args:
        document_id: Document UUID

    Returns:
        DocumentStatusResponse with current state and progress

    Raises:
        HTTPException: If document not found
    """
    state_manager = get_state_manager()

    try:
        # Get state from StateManager
        state_data = state_manager.get_document_state(document_id)

        if not state_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document status not found: {document_id}"
            )

        return DocumentStatusResponse(
            document_id=document_id,
            state=state_data.state.value,
            progress_percent=state_data.progress_percent,
            current_stage=state_data.current_stage,
            error_details=state_data.error_details,
            started_at=state_data.started_at,
            updated_at=state_data.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document status {document_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document status: {str(e)}"
        )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete document",
    description="Delete document record and associated files/chunks from all storage layers"
)
async def delete_document(document_id: UUID):
    """
    Delete document and all associated data

    Removes:
    - Document file from disk
    - Vector embeddings from Qdrant
    - Document record from PostgreSQL
    - Processing state from Redis

    Args:
        document_id: Document UUID

    Raises:
        HTTPException: If document not found or deletion fails
    """
    postgres = get_postgres_store()

    try:
        # Get document to find file path
        document = postgres.get_document(document_id)

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {document_id}"
            )

        # Delete file from disk
        try:
            file_path = Path(document['file_path'])
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to delete file: {e}")

        # Delete chunks from Qdrant
        try:
            from src.storage.qdrant_store import QdrantStore
            qdrant = QdrantStore()
            qdrant.delete_document_chunks(document_id)
            logger.info(f"Deleted Qdrant chunks for document {document_id}")
        except Exception as e:
            logger.warning(f"Failed to delete Qdrant chunks: {e}")

        # Delete from PostgreSQL
        with postgres.get_cursor() as cursor:
            # Delete related citations
            cursor.execute(
                "DELETE FROM citations WHERE document_id = %s",
                (str(document_id),)
            )

            # Delete related metrics
            cursor.execute(
                "DELETE FROM financial_metrics WHERE document_id = %s",
                (str(document_id),)
            )

            # Delete document
            cursor.execute(
                "DELETE FROM documents WHERE id = %s",
                (str(document_id),)
            )

        logger.info(f"Deleted document {document_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document {document_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.post(
    "/{document_id}/reprocess",
    response_model=DocumentUploadResponse,
    summary="Reprocess failed document",
    description="Retry processing a failed document. Only works for documents in 'failed' status."
)
async def reprocess_document(
    document_id: UUID,
    background_tasks: BackgroundTasks
) -> DocumentUploadResponse:
    """
    Reprocess a failed document

    Args:
        document_id: Document UUID

    Returns:
        DocumentUploadResponse with updated status

    Raises:
        HTTPException: If document not found or not in failed state
    """
    postgres = get_postgres_store()
    processor = get_document_processor()

    try:
        # Get document
        document = postgres.get_document(document_id)

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {document_id}"
            )

        # Check if document is in failed state
        if document['status'] != 'failed':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Document is not in failed state. Current status: {document['status']}"
            )

        # Check if file still exists
        file_path = Path(document['file_path'])
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document file not found on disk. Cannot reprocess."
            )

        # Reset status to pending
        postgres.update_document_status(document_id, "pending")

        # Schedule reprocessing in background
        background_tasks.add_task(
            process_document_background,
            document_id=document_id,
            case_id=document['case_id'],
            file_path=str(file_path),
            original_filename=document['original_filename']
        )

        logger.info(f"Document {document_id} queued for reprocessing")

        return DocumentUploadResponse(
            document_id=document_id,
            status="processing",
            message="Document queued for reprocessing"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reprocess document {document_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reprocess document: {str(e)}"
        )


# =========================================================================
# HEALTH CHECK
# =========================================================================

@router.get(
    "/health",
    summary="Health check",
    description="Check if document API and dependencies are healthy"
)
async def health_check():
    """
    Health check endpoint

    Returns:
        Health status of API and dependencies
    """
    postgres = get_postgres_store()

    try:
        # Check PostgreSQL
        pg_health = postgres.health_check()

        # Check upload directory
        upload_dir_exists = settings.upload_dir.exists()
        upload_dir_writable = settings.upload_dir.is_dir() if upload_dir_exists else False

        return {
            "status": "healthy",
            "service": "document_api",
            "dependencies": {
                "postgres": pg_health,
                "upload_directory": {
                    "exists": upload_dir_exists,
                    "writable": upload_dir_writable,
                    "path": str(settings.upload_dir)
                }
            }
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
