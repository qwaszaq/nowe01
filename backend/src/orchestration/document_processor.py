"""
Document Processing Orchestration Pipeline
Coordinates PDF extraction, chunking, embedding, and storage
"""

import logging
import time
import asyncio
import json
from typing import Dict, Any, Optional, List
from uuid import UUID
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict

from src.core.extractors.pdf_processor import PDFProcessor
from src.core.extractors.semantic_chunker import SemanticChunker
from src.core.extractors.docling_processor import DoclingProcessor
from src.core.extractors.structure_aware_chunker import StructureAwareChunker
from src.core.embeddings.e5_embeddings import E5Embeddings
from src.storage.qdrant_store import QdrantStore
from src.storage.postgres_store import PostgresStore
from src.storage.redis_store import RedisStore
from src.utils.document_classifier import DocumentClassifier, DocumentType

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Result of document processing"""
    document_id: UUID
    status: str  # "completed", "failed", "partial"
    chunk_count: int
    elapsed_time: float
    stages: Dict[str, Dict[str, Any]]  # Stage name -> {status, duration, error}
    error_message: Optional[str] = None


class DocumentProcessingError(Exception):
    """Base exception for document processing errors"""
    pass


class ValidationError(DocumentProcessingError):
    """Raised when document validation fails"""
    pass


class ExtractionError(DocumentProcessingError):
    """Raised when PDF extraction fails"""
    pass


class EmbeddingError(DocumentProcessingError):
    """Raised when embedding generation fails"""
    pass


class StorageError(DocumentProcessingError):
    """Raised when storage operations fail"""
    pass


class DocumentProcessor:
    """
    Document processing orchestration pipeline

    Workflow:
    1. Validate PDF
    2. Extract pages and metadata
    3. Chunk text with overlap
    4. Generate embeddings (batch processing)
    5. Store chunks+embeddings in Qdrant
    6. Store document metadata in Postgres
    7. Track state in Redis

    Features:
    - State tracking for each processing stage
    - Retry logic for embedding failures
    - Rollback on storage failures
    - Progress tracking via Redis
    - Comprehensive error handling and logging
    """

    # Processing states
    STATE_PENDING = "pending"
    STATE_VALIDATING = "validating"
    STATE_EXTRACTING = "extracting"
    STATE_CHUNKING = "chunking"
    STATE_EMBEDDING = "embedding"
    STATE_STORING = "storing"
    STATE_COMPLETED = "completed"
    STATE_FAILED = "failed"

    # Configuration
    DEFAULT_CHUNK_SIZE = 750
    DEFAULT_OVERLAP = 120
    DEFAULT_BATCH_SIZE = 32
    MAX_EMBEDDING_RETRIES = 3
    RETRY_DELAY = 2  # seconds

    def __init__(
        self,
        pdf_processor: Optional[PDFProcessor] = None,
        semantic_chunker: Optional[SemanticChunker] = None,
        docling_processor: Optional[DoclingProcessor] = None,
        structure_chunker: Optional[StructureAwareChunker] = None,
        document_classifier: Optional[DocumentClassifier] = None,
        embeddings: Optional[E5Embeddings] = None,
        qdrant_store: Optional[QdrantStore] = None,
        postgres_store: Optional[PostgresStore] = None,
        redis_store: Optional[RedisStore] = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_OVERLAP,
        batch_size: int = DEFAULT_BATCH_SIZE,
        use_docling_for_financial: bool = True
    ):
        """
        Initialize document processor with dependencies

        Args:
            pdf_processor: PDF extraction handler (optional, creates if None)
            semantic_chunker: Semantic chunking handler (optional, creates if None)
            docling_processor: Docling structure-aware processor (optional, creates if None)
            structure_chunker: Structure-aware chunker (optional, creates if None)
            document_classifier: Document type classifier (optional, creates if None)
            embeddings: E5 embeddings client (optional, creates if None)
            qdrant_store: Qdrant vector store (optional, creates if None)
            postgres_store: PostgreSQL store (optional, creates if None)
            redis_store: Redis cache (optional, creates if None)
            chunk_size: Characters per chunk (default: 750)
            overlap: Character overlap between chunks (default: 120)
            batch_size: Batch size for embedding generation (default: 32)
            use_docling_for_financial: Enable Docling for financial documents (default: True)
        """
        # Traditional processors (for general documents and backward compatibility)
        self.pdf_processor = pdf_processor or PDFProcessor()
        self.semantic_chunker = semantic_chunker or SemanticChunker(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            min_chunk_size=200
        )

        # NEW: Docling processors (for financial documents)
        self.use_docling_for_financial = use_docling_for_financial
        if self.use_docling_for_financial:
            self.docling_processor = docling_processor or DoclingProcessor()
            self.structure_chunker = structure_chunker or StructureAwareChunker(
                chunk_size=chunk_size,
                overlap=overlap,
                min_chunk_size=200
            )
        else:
            self.docling_processor = None
            self.structure_chunker = None

        # NEW: Document classifier
        self.document_classifier = document_classifier or DocumentClassifier()

        # Common dependencies
        self.embeddings = embeddings or E5Embeddings()
        self.qdrant_store = qdrant_store or QdrantStore()
        self.postgres_store = postgres_store or PostgresStore()
        self.redis_store = redis_store or RedisStore()

        self.chunk_size = chunk_size
        self.overlap = overlap
        self.batch_size = batch_size

        logger.info(
            f"DocumentProcessor initialized: chunk_size={chunk_size}, "
            f"overlap={overlap}, batch_size={batch_size}, "
            f"docling_enabled={self.use_docling_for_financial}"
        )

    async def process_document(
        self,
        case_id: UUID,
        document_path: str,
        document_metadata: Optional[Dict[str, Any]] = None
    ) -> ProcessingResult:
        """
        Process document through complete pipeline

        Args:
            case_id: Case UUID
            document_path: Absolute path to PDF file
            document_metadata: Optional metadata dict with keys:
                - document_id: UUID (if already created in DB)
                - original_filename: str
                - document_type: str (default: "financial")
                - Any other custom metadata

        Returns:
            ProcessingResult with status, timing, and chunk count

        Raises:
            DocumentProcessingError: On processing failure
        """
        start_time = time.time()
        document_path_obj = Path(document_path)
        document_metadata = document_metadata or {}

        # Get or create document_id
        document_id = document_metadata.get('document_id')
        if not document_id:
            raise ValueError("document_id must be provided in document_metadata")

        stages: Dict[str, Dict[str, Any]] = {}

        # Get original filename for classification
        original_filename = document_metadata.get('original_filename', document_path_obj.name)

        logger.info(
            f"Starting document processing: document_id={document_id}, "
            f"case_id={case_id}, path={document_path}, filename={original_filename}"
        )

        try:
            # Update state to pending
            await self._update_state(document_id, self.STATE_PENDING)

            # =====================================================================
            # STAGE 0: DOCUMENT CLASSIFICATION (NEW)
            # =====================================================================
            # Classify document to route to appropriate processor
            document_type: DocumentType = self.document_classifier.classify(
                filename=original_filename
            )

            logger.info(
                f"Document classified as: {document_type.upper()} "
                f"(filename: {original_filename})"
            )

            # Determine which processors to use based on type and feature flag
            use_docling = (
                document_type == "financial"
                and self.use_docling_for_financial
                and self.docling_processor is not None
            )

            if use_docling:
                logger.info(
                    f"Routing to DOCLING pipeline "
                    f"(structure-aware extraction + table-preserving chunking)"
                )
            else:
                logger.info(
                    f"Routing to PYMUPDF pipeline "
                    f"(fast text extraction + semantic chunking)"
                )

            # Store document type in metadata
            document_metadata['document_type'] = document_type
            document_metadata['used_docling'] = use_docling

            # =====================================================================
            # STAGE 1: VALIDATION
            # =====================================================================
            stage_start = time.time()
            await self._update_state(document_id, self.STATE_VALIDATING)

            try:
                validation = self.pdf_processor.validate_pdf(document_path)
                if not validation['valid']:
                    error_msg = "; ".join(validation['errors'])
                    raise ValidationError(f"PDF validation failed: {error_msg}")

                if validation.get('warnings'):
                    for warning in validation['warnings']:
                        logger.warning(f"Validation warning for {document_id}: {warning}")

                stages['validation'] = {
                    'status': 'completed',
                    'duration': time.time() - stage_start,
                    'info': validation['info']
                }

                logger.info(f"Validation completed: {validation['info']}")

            except Exception as e:
                stages['validation'] = {
                    'status': 'failed',
                    'duration': time.time() - stage_start,
                    'error': str(e)
                }
                raise ValidationError(f"Validation failed: {e}") from e

            # =====================================================================
            # STAGE 2: EXTRACTION (ROUTED)
            # =====================================================================
            stage_start = time.time()
            await self._update_state(document_id, self.STATE_EXTRACTING)

            try:
                # Run blocking PDF extraction in thread pool to avoid blocking event loop
                if use_docling:
                    logger.info("Using DoclingProcessor for structure-aware extraction...")
                    extracted = await asyncio.to_thread(
                        self.docling_processor.extract_all,
                        document_path
                    )
                else:
                    logger.info("Using PDFProcessor for fast text extraction...")
                    extracted = await asyncio.to_thread(
                        self.pdf_processor.extract_all,
                        document_path
                    )

                pages = extracted['pages']

                if not pages:
                    raise ExtractionError("No text extracted from PDF")

                stages['extraction'] = {
                    'status': 'completed',
                    'duration': time.time() - stage_start,
                    'stats': extracted.get('extraction_stats', {}),
                    'processor': 'docling' if use_docling else 'pymupdf'
                }

                logger.info(
                    f"Extraction completed ({stages['extraction']['processor']}): "
                    f"{len(pages)} pages, "
                    f"{extracted.get('extraction_stats', {}).get('total_characters', 'N/A')} chars"
                )

            except Exception as e:
                stages['extraction'] = {
                    'status': 'failed',
                    'duration': time.time() - stage_start,
                    'error': str(e)
                }
                raise ExtractionError(f"PDF extraction failed: {e}") from e

            # =====================================================================
            # STAGE 3: CHUNKING (ROUTED)
            # =====================================================================
            stage_start = time.time()
            await self._update_state(document_id, self.STATE_CHUNKING)
            logger.info(f"Starting chunking for {len(pages)} pages...")

            try:
                # Route to appropriate chunker
                if use_docling:
                    logger.info("Using StructureAwareChunker for table-preserving chunking...")
                    chunks = self.structure_chunker.chunk_document(extracted)
                else:
                    logger.info("Using SemanticChunker for semantic boundary chunking...")
                    chunks = self.semantic_chunker.chunk_pages(pages)

                logger.info(f"Chunking returned {len(chunks) if chunks else 0} chunks")

                if not chunks:
                    raise DocumentProcessingError("No chunks created from pages")

                # Get chunk statistics (both chunkers support this)
                if use_docling:
                    chunk_stats = self.structure_chunker.get_chunk_statistics(chunks)
                else:
                    chunk_stats = self.semantic_chunker.get_chunk_statistics(chunks)

                stages['chunking'] = {
                    'status': 'completed',
                    'duration': time.time() - stage_start,
                    'chunk_count': len(chunks),
                    'stats': chunk_stats,
                    'chunker': 'structure_aware' if use_docling else 'semantic'
                }

                logger.info(
                    f"Chunking completed ({stages['chunking']['chunker']}): "
                    f"{len(chunks)} chunks, "
                    f"avg size: {chunk_stats.get('avg_chunk_size', 0):.1f} chars"
                )

            except Exception as e:
                stages['chunking'] = {
                    'status': 'failed',
                    'duration': time.time() - stage_start,
                    'error': str(e)
                }
                raise DocumentProcessingError(f"Chunking failed: {e}") from e

            # =====================================================================
            # STAGE 4: EMBEDDING
            # =====================================================================
            stage_start = time.time()
            await self._update_state(document_id, self.STATE_EMBEDDING)

            embeddings_list = []
            try:
                # Generate embeddings with retry logic
                embeddings_list = await self._generate_embeddings_with_retry(
                    chunks=chunks,
                    document_id=document_id
                )

                stages['embedding'] = {
                    'status': 'completed',
                    'duration': time.time() - stage_start,
                    'embeddings_count': len(embeddings_list),
                    'dimensions': len(embeddings_list[0]) if embeddings_list else 0
                }

                logger.info(
                    f"Embedding completed: {len(embeddings_list)} vectors, "
                    f"{len(embeddings_list[0])}D"
                )

            except Exception as e:
                stages['embedding'] = {
                    'status': 'failed',
                    'duration': time.time() - stage_start,
                    'error': str(e)
                }
                raise EmbeddingError(f"Embedding generation failed: {e}") from e

            # =====================================================================
            # STAGE 5: STORAGE
            # =====================================================================
            stage_start = time.time()
            await self._update_state(document_id, self.STATE_STORING)

            try:
                # Store chunks+embeddings in Qdrant
                stored_count = self.qdrant_store.store_chunks(
                    case_id=case_id,
                    document_id=document_id,
                    chunks=chunks,
                    embeddings=embeddings_list
                )

                # Update document metadata in Postgres
                # Prepare metadata
                metadata = {
                    **document_metadata.get('metadata', {}),
                    'extraction_stats': extracted['extraction_stats'],
                    'chunk_stats': chunk_stats,
                    'processing_completed_at': datetime.now().isoformat()
                }

                # Store table info if tables were extracted
                if extracted.get('tables'):
                    metadata['tables_count'] = len(extracted['tables'])

                # Update document with status, pages_count, and metadata
                self.postgres_store.update_document_status(
                    document_id=document_id,
                    status='completed',
                    pages_count=extracted['extraction_stats']['total_pages'],
                    metadata=metadata
                )

                stages['storage'] = {
                    'status': 'completed',
                    'duration': time.time() - stage_start,
                    'chunks_stored': stored_count,
                    'qdrant': 'success',
                    'postgres': 'success'
                }

                logger.info(
                    f"Storage completed: {stored_count} chunks stored in Qdrant, "
                    f"metadata updated in Postgres"
                )

            except Exception as e:
                stages['storage'] = {
                    'status': 'failed',
                    'duration': time.time() - stage_start,
                    'error': str(e)
                }

                # Attempt rollback
                await self._rollback_storage(document_id, case_id)

                raise StorageError(f"Storage failed: {e}") from e

            # =====================================================================
            # SUCCESS
            # =====================================================================
            await self._update_state(document_id, self.STATE_COMPLETED)

            elapsed_time = time.time() - start_time

            result = ProcessingResult(
                document_id=document_id,
                status='completed',
                chunk_count=len(chunks),
                elapsed_time=elapsed_time,
                stages=stages
            )

            logger.info(
                f"Document processing completed successfully: document_id={document_id}, "
                f"chunks={len(chunks)}, elapsed={elapsed_time:.2f}s"
            )

            return result

        except DocumentProcessingError as e:
            # Update state to failed
            await self._update_state(document_id, self.STATE_FAILED, error=str(e))

            # Update Postgres status
            try:
                self.postgres_store.update_document_status(
                    document_id=document_id,
                    status='failed'
                )
            except Exception as db_error:
                logger.error(f"Failed to update document status in DB: {db_error}")

            elapsed_time = time.time() - start_time

            result = ProcessingResult(
                document_id=document_id,
                status='failed',
                chunk_count=0,
                elapsed_time=elapsed_time,
                stages=stages,
                error_message=str(e)
            )

            logger.error(
                f"Document processing failed: document_id={document_id}, "
                f"error={str(e)}, elapsed={elapsed_time:.2f}s"
            )

            return result

        except Exception as e:
            # Unexpected error
            await self._update_state(document_id, self.STATE_FAILED, error=str(e))

            elapsed_time = time.time() - start_time

            logger.error(
                f"Unexpected error processing document {document_id}: {e}",
                exc_info=True
            )

            result = ProcessingResult(
                document_id=document_id,
                status='failed',
                chunk_count=0,
                elapsed_time=elapsed_time,
                stages=stages,
                error_message=f"Unexpected error: {str(e)}"
            )

            return result

    async def reprocess_document(
        self,
        document_id: UUID
    ) -> ProcessingResult:
        """
        Reprocess a failed document

        Args:
            document_id: Document UUID

        Returns:
            ProcessingResult

        Raises:
            ValueError: If document not found or not in failed state
        """
        logger.info(f"Reprocessing document: {document_id}")

        # Get document from database
        document = self.postgres_store.get_document(document_id)
        if not document:
            raise ValueError(f"Document not found: {document_id}")

        # Check if document is in failed state
        if document['status'] != 'failed':
            raise ValueError(
                f"Document {document_id} is not in failed state (status: {document['status']})"
            )

        # Clean up any partial data
        await self._rollback_storage(document_id, document['case_id'])

        # Reprocess document
        return await self.process_document(
            case_id=document['case_id'],
            document_path=document['file_path'],
            document_metadata={
                'document_id': document_id,
                'original_filename': document['original_filename'],
                'document_type': document.get('document_type', 'financial'),
                'metadata': document.get('metadata', {})
            }
        )

    async def get_processing_status(
        self,
        document_id: UUID
    ) -> Dict[str, Any]:
        """
        Get current processing status for a document

        Args:
            document_id: Document UUID

        Returns:
            Dict with current state, progress, and metadata
        """
        # Get state from Redis
        state_key = f"doc:{document_id}:state"
        state_data = self.redis_store.hash_get_all(state_key)

        if not state_data:
            # Fall back to Postgres
            document = self.postgres_store.get_document(document_id)
            if document:
                return {
                    'document_id': str(document_id),
                    'state': document['status'],
                    'source': 'postgres'
                }
            else:
                return {
                    'document_id': str(document_id),
                    'state': 'unknown',
                    'error': 'Document not found'
                }

        return {
            'document_id': str(document_id),
            'state': state_data.get('state', 'unknown'),
            'updated_at': state_data.get('updated_at'),
            'error': state_data.get('error'),
            'source': 'redis'
        }

    async def _generate_embeddings_with_retry(
        self,
        chunks: List[Dict[str, Any]],
        document_id: UUID
    ) -> List[List[float]]:
        """
        Generate embeddings with retry logic

        Args:
            chunks: List of text chunks
            document_id: Document UUID for logging

        Returns:
            List of embedding vectors

        Raises:
            EmbeddingError: If all retries fail
        """
        for attempt in range(1, self.MAX_EMBEDDING_RETRIES + 1):
            try:
                logger.info(
                    f"Generating embeddings for document {document_id} "
                    f"(attempt {attempt}/{self.MAX_EMBEDDING_RETRIES})"
                )

                embeddings = await self.embeddings.embed_chunks(
                    chunks=chunks,
                    batch_size=self.batch_size
                )

                return embeddings

            except Exception as e:
                logger.error(
                    f"Embedding attempt {attempt}/{self.MAX_EMBEDDING_RETRIES} failed "
                    f"for document {document_id}: {e}"
                )

                if attempt < self.MAX_EMBEDDING_RETRIES:
                    # Wait before retry
                    delay = self.RETRY_DELAY * attempt
                    logger.info(f"Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    # All retries exhausted
                    raise EmbeddingError(
                        f"Failed to generate embeddings after {self.MAX_EMBEDDING_RETRIES} attempts: {e}"
                    ) from e

    async def _update_state(
        self,
        document_id: UUID,
        state: str,
        error: Optional[str] = None
    ) -> None:
        """
        Update processing state in Redis

        Args:
            document_id: Document UUID
            state: Current processing state
            error: Optional error message
        """
        state_key = f"doc:{document_id}:state"

        state_data = {
            'state': state,
            'updated_at': datetime.now().isoformat()
        }

        if error:
            state_data['error'] = error

        # Store in Redis as hash (run synchronous Redis calls in thread pool)
        def update_redis():
            for field, value in state_data.items():
                self.redis_store.hash_set(state_key, field, value)
            # Set TTL (24 hours)
            self.redis_store.client.expire(f"{self.redis_store._make_key(state_key)}", 86400)

        await asyncio.to_thread(update_redis)

        logger.debug(f"State updated for document {document_id}: {state}")

    async def _rollback_storage(
        self,
        document_id: UUID,
        case_id: UUID
    ) -> None:
        """
        Rollback partial storage on failure

        Args:
            document_id: Document UUID
            case_id: Case UUID
        """
        logger.warning(f"Rolling back partial storage for document {document_id}")

        try:
            # Delete chunks from Qdrant
            qdrant_result = self.qdrant_store.delete_document_chunks(document_id)
            if qdrant_result:
                logger.info(f"Cleaned up Qdrant chunks for document {document_id}")

            # Update document status in Postgres
            self.postgres_store.update_document_status(
                document_id=document_id,
                status='failed'
            )

            logger.info(f"Rollback completed for document {document_id}")

        except Exception as e:
            logger.error(
                f"Error during rollback for document {document_id}: {e}",
                exc_info=True
            )

    async def close(self):
        """Close all connections"""
        logger.info("Closing DocumentProcessor connections")

        if hasattr(self.embeddings, 'close'):
            await self.embeddings.close()

        if hasattr(self.qdrant_store, 'close'):
            self.qdrant_store.close()

        if hasattr(self.postgres_store, 'close'):
            self.postgres_store.close()

        if hasattr(self.redis_store, 'close'):
            self.redis_store.close()

        logger.info("DocumentProcessor connections closed")

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
