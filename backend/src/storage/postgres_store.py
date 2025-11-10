"""
PostgreSQL Storage Layer
Handles all structured data storage
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import UUID
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values, Json
from psycopg2.pool import ThreadedConnectionPool
from contextlib import contextmanager

from src.config import settings

logger = logging.getLogger(__name__)


class PostgresStore:
    """PostgreSQL storage manager with connection pooling"""

    def __init__(self):
        self.connection_pool = None
        self._initialize_pool()

    def _initialize_pool(self):
        """Initialize connection pool"""
        try:
            self.connection_pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=settings.postgres_pool_size,
                host=settings.postgres_host,
                port=settings.postgres_port,
                database=settings.postgres_db,
                user=settings.postgres_user,
                password=settings.postgres_password
            )
            logger.info("PostgreSQL connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL pool: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """Get connection from pool"""
        conn = self.connection_pool.getconn()
        try:
            yield conn
        finally:
            self.connection_pool.putconn(conn)

    @contextmanager
    def get_cursor(self, dict_cursor=True):
        """Get cursor with automatic connection management"""
        with self.get_connection() as conn:
            cursor_factory = RealDictCursor if dict_cursor else None
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Database error: {e}")
                raise
            finally:
                cursor.close()

    # =========================================================================
    # CASES
    # =========================================================================

    def create_case(
        self,
        name: str,
        description: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> UUID:
        """Create new investigation case"""
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO cases (name, description, metadata)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (name, description, Json(metadata or {}))
            )
            result = cursor.fetchone()
            case_id = result['id']
            logger.info(f"Created case: {case_id} - {name}")
            return case_id

    def get_case(self, case_id: UUID) -> Optional[Dict]:
        """Get case by ID"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM cases WHERE id = %s",
                (str(case_id),)
            )
            return cursor.fetchone()

    def list_cases(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """List all cases with optional filtering"""
        with self.get_cursor() as cursor:
            if status:
                cursor.execute(
                    """
                    SELECT * FROM cases
                    WHERE status = %s
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (status, limit, offset)
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM cases
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (limit, offset)
                )
            return cursor.fetchall()

    def update_case(self, case_id: UUID, **kwargs) -> bool:
        """Update case fields"""
        allowed_fields = ['name', 'description', 'status', 'metadata']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not updates:
            return False

        set_clause = ', '.join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values()) + [str(case_id)]

        with self.get_cursor() as cursor:
            cursor.execute(
                f"UPDATE cases SET {set_clause} WHERE id = %s",
                values
            )
            return cursor.rowcount > 0

    # =========================================================================
    # DOCUMENTS
    # =========================================================================

    def create_document(
        self,
        case_id: UUID,
        filename: str,
        original_filename: str,
        file_path: str,
        file_size: int,
        **kwargs
    ) -> UUID:
        """Create document record"""
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO documents
                (case_id, filename, original_filename, file_path, file_size,
                 document_type, mime_type, pages_count, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    str(case_id),
                    filename,
                    original_filename,
                    file_path,
                    file_size,
                    kwargs.get('document_type', 'financial'),
                    kwargs.get('mime_type', 'application/pdf'),
                    kwargs.get('pages_count'),
                    Json(kwargs.get('metadata', {}))
                )
            )
            doc_id = cursor.fetchone()['id']
            logger.info(f"Created document: {doc_id} - {original_filename}")
            return doc_id

    def get_document(self, document_id: UUID) -> Optional[Dict]:
        """Get document by ID"""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM documents WHERE id = %s",
                (str(document_id),)
            )
            return cursor.fetchone()

    def list_documents(self, case_id: UUID) -> List[Dict]:
        """List all documents for a case"""
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM documents
                WHERE case_id = %s
                ORDER BY created_at DESC
                """,
                (str(case_id),)
            )
            return cursor.fetchall()

    def update_document_status(
        self,
        document_id: UUID,
        status: str,
        **kwargs
    ) -> bool:
        """Update document processing status"""
        with self.get_cursor() as cursor:
            timestamp_field = None
            if status == 'processing':
                timestamp_field = 'processing_started_at'
            elif status in ['completed', 'failed']:
                timestamp_field = 'processing_completed_at'

            if timestamp_field:
                cursor.execute(
                    f"""
                    UPDATE documents
                    SET status = %s, {timestamp_field} = %s
                    WHERE id = %s
                    """,
                    (status, datetime.now(), str(document_id))
                )
            else:
                cursor.execute(
                    "UPDATE documents SET status = %s WHERE id = %s",
                    (status, str(document_id))
                )

            return cursor.rowcount > 0

    # =========================================================================
    # FINANCIAL METRICS
    # =========================================================================

    def store_metrics(
        self,
        document_id: UUID,
        metrics: List[Dict[str, Any]]
    ) -> int:
        """Store multiple financial metrics"""
        if not metrics:
            return 0

        with self.get_cursor() as cursor:
            values = [
                (
                    str(document_id),
                    m['metric_name'],
                    m.get('metric_value'),
                    m.get('metric_unit'),
                    m.get('fiscal_year'),
                    m.get('fiscal_period'),
                    m.get('page_number'),
                    m.get('confidence'),
                    m.get('calculation_method')
                )
                for m in metrics
            ]

            execute_values(
                cursor,
                """
                INSERT INTO financial_metrics
                (document_id, metric_name, metric_value, metric_unit,
                 fiscal_year, fiscal_period, page_number, confidence,
                 calculation_method)
                VALUES %s
                """,
                values
            )

            count = cursor.rowcount
            logger.info(f"Stored {count} metrics for document {document_id}")
            return count

    def get_metrics(
        self,
        document_id: UUID,
        metric_names: Optional[List[str]] = None
    ) -> List[Dict]:
        """Get financial metrics for document"""
        with self.get_cursor() as cursor:
            if metric_names:
                placeholders = ','.join(['%s'] * len(metric_names))
                cursor.execute(
                    f"""
                    SELECT * FROM financial_metrics
                    WHERE document_id = %s AND metric_name IN ({placeholders})
                    ORDER BY fiscal_year DESC, metric_name
                    """,
                    (str(document_id), *metric_names)
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM financial_metrics
                    WHERE document_id = %s
                    ORDER BY fiscal_year DESC, metric_name
                    """,
                    (str(document_id),)
                )
            return cursor.fetchall()

    # =========================================================================
    # CITATIONS
    # =========================================================================

    def store_citation(
        self,
        document_id: UUID,
        page_number: int,
        text_excerpt: str,
        metric_id: Optional[UUID] = None,
        **kwargs
    ) -> UUID:
        """Store citation"""
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO citations
                (metric_id, document_id, page_number, text_excerpt,
                 context_before, context_after, bbox)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    str(metric_id) if metric_id else None,
                    str(document_id),
                    page_number,
                    text_excerpt,
                    kwargs.get('context_before'),
                    kwargs.get('context_after'),
                    kwargs.get('bbox')
                )
            )
            return cursor.fetchone()['id']

    def get_citations(
        self,
        document_id: Optional[UUID] = None,
        metric_id: Optional[UUID] = None
    ) -> List[Dict]:
        """Get citations"""
        with self.get_cursor() as cursor:
            if metric_id:
                cursor.execute(
                    "SELECT * FROM citations WHERE metric_id = %s",
                    (str(metric_id),)
                )
            elif document_id:
                cursor.execute(
                    "SELECT * FROM citations WHERE document_id = %s",
                    (str(document_id),)
                )
            else:
                return []

            return cursor.fetchall()

    # =========================================================================
    # ANALYSIS RESULTS
    # =========================================================================

    def store_analysis_result(
        self,
        case_id: UUID,
        analysis_type: str,
        result_data: Dict,
        **kwargs
    ) -> UUID:
        """Store analysis result"""
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO analysis_results
                (case_id, analysis_type, result_data, executive_summary,
                 deep_dive_report, quality_score, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    str(case_id),
                    analysis_type,
                    Json(result_data),
                    kwargs.get('executive_summary'),
                    kwargs.get('deep_dive_report'),
                    kwargs.get('quality_score'),
                    Json(kwargs.get('metadata', {}))
                )
            )
            return cursor.fetchone()['id']

    def get_analysis_results(self, case_id: UUID) -> List[Dict]:
        """Get all analysis results for case"""
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM analysis_results
                WHERE case_id = %s
                ORDER BY created_at DESC
                """,
                (str(case_id),)
            )
            return cursor.fetchall()

    # =========================================================================
    # PROCESSING STATUS
    # =========================================================================

    def update_processing_status(
        self,
        document_id: UUID,
        stage: str,
        status: str,
        progress: int = 0,
        message: Optional[str] = None,
        error: Optional[str] = None
    ) -> None:
        """Update processing status"""
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO processing_status
                (document_id, stage, status, progress, message, error, started_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (str(document_id), stage, status, progress, message, error, datetime.now())
            )

    def get_processing_status(self, document_id: UUID) -> List[Dict]:
        """Get processing status history"""
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM processing_status
                WHERE document_id = %s
                ORDER BY created_at DESC
                """,
                (str(document_id),)
            )
            return cursor.fetchall()

    # =========================================================================
    # HEALTH CHECK
    # =========================================================================

    def health_check(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                return {
                    "status": "healthy",
                    "database": settings.postgres_db,
                    "host": settings.postgres_host
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    def close(self):
        """Close connection pool"""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("PostgreSQL connection pool closed")
