"""
State Management System for Document Processing and Analysis
Tracks document lifecycle states and analysis workflow states with Redis caching and PostgreSQL persistence
"""

import logging
import json
from typing import Dict, List, Any, Optional, Literal
from datetime import datetime, timedelta
from uuid import UUID
from enum import Enum
from dataclasses import dataclass, asdict
from contextlib import contextmanager

from src.config import settings
from src.storage.redis_store import RedisStore
from src.storage.postgres_store import PostgresStore

logger = logging.getLogger(__name__)


# =========================================================================
# STATE ENUMS AND DATA CLASSES
# =========================================================================

class DocumentState(str, Enum):
    """Valid document processing states"""
    PENDING = "pending"
    EXTRACTING = "extracting"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    STORING = "storing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisState(str, Enum):
    """Valid analysis workflow states"""
    QUEUED = "queued"
    SEARCHING = "searching"
    CALCULATING = "calculating"
    CLASSIFYING = "classifying"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class DocumentStateData:
    """Document state information"""
    document_id: str
    state: DocumentState
    progress_percent: float
    current_stage: str
    started_at: datetime
    updated_at: datetime
    error_details: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['state'] = self.state.value
        data['started_at'] = self.started_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentStateData':
        """Create from dictionary"""
        data['state'] = DocumentState(data['state'])
        data['started_at'] = datetime.fromisoformat(data['started_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


@dataclass
class AnalysisStateData:
    """Analysis state information"""
    analysis_id: str
    case_id: str
    state: AnalysisState
    progress_percent: float
    current_stage: str
    started_at: datetime
    updated_at: datetime
    results: Optional[Dict[str, Any]] = None
    error_details: Optional[str] = None
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['state'] = self.state.value
        data['started_at'] = self.started_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisStateData':
        """Create from dictionary"""
        data['state'] = AnalysisState(data['state'])
        data['started_at'] = datetime.fromisoformat(data['started_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


@dataclass
class ProcessingStats:
    """Processing statistics"""
    total_documents: int
    pending: int
    extracting: int
    chunking: int
    embedding: int
    storing: int
    completed: int
    failed: int
    success_rate: float
    avg_processing_time_seconds: Optional[float]
    error_rate: float
    errors_by_type: Dict[str, int]
    case_id: Optional[str] = None


# =========================================================================
# STATE TRANSITION VALIDATION
# =========================================================================

# Valid state transitions for documents
DOCUMENT_STATE_TRANSITIONS = {
    DocumentState.PENDING: [DocumentState.EXTRACTING, DocumentState.FAILED],
    DocumentState.EXTRACTING: [DocumentState.CHUNKING, DocumentState.FAILED],
    DocumentState.CHUNKING: [DocumentState.EMBEDDING, DocumentState.FAILED],
    DocumentState.EMBEDDING: [DocumentState.STORING, DocumentState.FAILED],
    DocumentState.STORING: [DocumentState.COMPLETED, DocumentState.FAILED],
    DocumentState.COMPLETED: [],  # Terminal state
    DocumentState.FAILED: [DocumentState.PENDING],  # Can retry
}

# Valid state transitions for analysis
ANALYSIS_STATE_TRANSITIONS = {
    AnalysisState.QUEUED: [AnalysisState.SEARCHING, AnalysisState.FAILED],
    AnalysisState.SEARCHING: [AnalysisState.CALCULATING, AnalysisState.FAILED],
    AnalysisState.CALCULATING: [AnalysisState.CLASSIFYING, AnalysisState.FAILED],
    AnalysisState.CLASSIFYING: [AnalysisState.COMPLETED, AnalysisState.FAILED],
    AnalysisState.COMPLETED: [],  # Terminal state
    AnalysisState.FAILED: [AnalysisState.QUEUED],  # Can retry
}


# =========================================================================
# STATE MANAGER CLASS
# =========================================================================

class StateManager:
    """
    Manages state for document processing and analysis workflows

    Uses Redis for fast caching with TTL and PostgreSQL for persistence.
    Emits state change events via Redis pub/sub for real-time monitoring.
    """

    # Redis key patterns
    KEY_DOCUMENT_STATE = "state:document:{document_id}"
    KEY_ANALYSIS_STATE = "state:analysis:{analysis_id}"
    KEY_DOCUMENT_TIMING = "timing:document:{document_id}"
    KEY_ERROR_COUNT = "errors:{error_type}"

    # TTL values
    TTL_DOCUMENT_STATE = 86400  # 24 hours
    TTL_ANALYSIS_STATE = 3600  # 1 hour
    TTL_TIMING_DATA = 604800  # 7 days

    # Pub/sub channels
    CHANNEL_STATE_CHANGES = "state_changes"
    CHANNEL_ALERTS = "state_alerts"

    def __init__(
        self,
        redis_store: Optional[RedisStore] = None,
        postgres_store: Optional[PostgresStore] = None
    ):
        """
        Initialize state manager

        Args:
            redis_store: Redis storage instance (creates new if None)
            postgres_store: PostgreSQL storage instance (creates new if None)
        """
        self.redis = redis_store or RedisStore()
        self.postgres = postgres_store or PostgresStore()
        logger.info("StateManager initialized")

    # =========================================================================
    # DOCUMENT STATE MANAGEMENT
    # =========================================================================

    def set_document_state(
        self,
        document_id: UUID,
        state: DocumentState,
        metadata: Optional[Dict[str, Any]] = None,
        progress_percent: float = 0.0,
        error_details: Optional[str] = None
    ) -> bool:
        """
        Set document processing state

        Args:
            document_id: Document identifier
            state: New state
            metadata: Optional metadata dict
            progress_percent: Progress percentage (0-100)
            error_details: Error message if state is FAILED

        Returns:
            True if state was set successfully

        Raises:
            ValueError: If state transition is invalid
        """
        doc_id_str = str(document_id)

        # Validate state transition
        current_state_data = self.get_document_state(document_id)
        if current_state_data:
            current_state = current_state_data.state
            if not self._is_valid_document_transition(current_state, state):
                error_msg = f"Invalid state transition: {current_state.value} -> {state.value}"
                logger.warning(f"Document {doc_id_str}: {error_msg}")
                raise ValueError(error_msg)

        # Create state data
        now = datetime.now()
        state_data = DocumentStateData(
            document_id=doc_id_str,
            state=state,
            progress_percent=progress_percent,
            current_stage=state.value,
            started_at=current_state_data.started_at if current_state_data else now,
            updated_at=now,
            error_details=error_details,
            retry_count=current_state_data.retry_count if current_state_data else 0,
            metadata=metadata or {}
        )

        # Store in Redis with TTL
        redis_key = self.KEY_DOCUMENT_STATE.format(document_id=doc_id_str)
        redis_success = self.redis.setex(
            redis_key,
            self.TTL_DOCUMENT_STATE,
            json.dumps(state_data.to_dict())
        )

        # Update PostgreSQL
        postgres_success = self.postgres.update_document_status(
            document_id,
            state.value,
            error=error_details if error_details else None
        )

        # Track timing if starting or completing
        if state == DocumentState.PENDING:
            self._start_timing(document_id, "document_processing")
        elif state == DocumentState.COMPLETED:
            self._end_timing(document_id, "document_processing")

        # Emit state change event
        if current_state_data:
            self._emit_state_change_event(
                entity_type="document",
                entity_id=doc_id_str,
                old_state=current_state_data.state.value,
                new_state=state.value,
                metadata=metadata or {}
            )

        # Alert on failure
        if state == DocumentState.FAILED:
            self._emit_alert(
                alert_type="document_failed",
                entity_id=doc_id_str,
                message=error_details or "Document processing failed",
                severity="error"
            )

        logger.info(f"Document {doc_id_str} state: {state.value} (progress: {progress_percent:.1f}%)")

        return redis_success and postgres_success

    def get_document_state(self, document_id: UUID) -> Optional[DocumentStateData]:
        """
        Get document processing state

        Checks Redis first (fast), falls back to PostgreSQL if not cached

        Args:
            document_id: Document identifier

        Returns:
            DocumentStateData or None if not found
        """
        doc_id_str = str(document_id)

        # Try Redis first
        redis_key = self.KEY_DOCUMENT_STATE.format(document_id=doc_id_str)
        cached_data = self.redis.get(redis_key)

        if cached_data:
            try:
                data = json.loads(cached_data)
                return DocumentStateData.from_dict(data)
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.error(f"Failed to parse cached document state: {e}")

        # Fallback to PostgreSQL
        doc_record = self.postgres.get_document(document_id)
        if not doc_record:
            return None

        # Reconstruct state from database
        try:
            state = DocumentState(doc_record.get('status', 'pending'))
        except ValueError:
            state = DocumentState.PENDING

        state_data = DocumentStateData(
            document_id=doc_id_str,
            state=state,
            progress_percent=100.0 if state == DocumentState.COMPLETED else 0.0,
            current_stage=state.value,
            started_at=doc_record.get('created_at', datetime.now()),
            updated_at=doc_record.get('updated_at', datetime.now()),
            retry_count=0,
            metadata=doc_record.get('metadata', {})
        )

        # Cache for future lookups
        self.redis.setex(
            redis_key,
            self.TTL_DOCUMENT_STATE,
            json.dumps(state_data.to_dict())
        )

        return state_data

    # =========================================================================
    # ANALYSIS STATE MANAGEMENT
    # =========================================================================

    def set_analysis_state(
        self,
        analysis_id: str,
        case_id: UUID,
        state: AnalysisState,
        results: Optional[Dict[str, Any]] = None,
        progress_percent: float = 0.0,
        error_details: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Set analysis workflow state

        Args:
            analysis_id: Analysis identifier
            case_id: Case identifier
            state: New state
            results: Analysis results (if completed)
            progress_percent: Progress percentage (0-100)
            error_details: Error message if state is FAILED
            metadata: Optional metadata dict

        Returns:
            True if state was set successfully

        Raises:
            ValueError: If state transition is invalid
        """
        # Validate state transition
        current_state_data = self.get_analysis_state(analysis_id)
        if current_state_data:
            current_state = current_state_data.state
            if not self._is_valid_analysis_transition(current_state, state):
                error_msg = f"Invalid state transition: {current_state.value} -> {state.value}"
                logger.warning(f"Analysis {analysis_id}: {error_msg}")
                raise ValueError(error_msg)

        # Create state data
        now = datetime.now()
        state_data = AnalysisStateData(
            analysis_id=analysis_id,
            case_id=str(case_id),
            state=state,
            progress_percent=progress_percent,
            current_stage=state.value,
            started_at=current_state_data.started_at if current_state_data else now,
            updated_at=now,
            results=results,
            error_details=error_details,
            metadata=metadata or {}
        )

        # Store in Redis with TTL
        redis_key = self.KEY_ANALYSIS_STATE.format(analysis_id=analysis_id)
        redis_success = self.redis.setex(
            redis_key,
            self.TTL_ANALYSIS_STATE,
            json.dumps(state_data.to_dict())
        )

        # Track timing
        if state == AnalysisState.QUEUED:
            self._start_timing(analysis_id, "analysis")
        elif state == AnalysisState.COMPLETED:
            self._end_timing(analysis_id, "analysis")

        # Emit state change event
        if current_state_data:
            self._emit_state_change_event(
                entity_type="analysis",
                entity_id=analysis_id,
                old_state=current_state_data.state.value,
                new_state=state.value,
                metadata=metadata or {}
            )

        # Alert on failure
        if state == AnalysisState.FAILED:
            self._emit_alert(
                alert_type="analysis_failed",
                entity_id=analysis_id,
                message=error_details or "Analysis failed",
                severity="error"
            )

        logger.info(f"Analysis {analysis_id} state: {state.value} (progress: {progress_percent:.1f}%)")

        return redis_success

    def get_analysis_state(self, analysis_id: str) -> Optional[AnalysisStateData]:
        """
        Get analysis workflow state

        Args:
            analysis_id: Analysis identifier

        Returns:
            AnalysisStateData or None if not found
        """
        redis_key = self.KEY_ANALYSIS_STATE.format(analysis_id=analysis_id)
        cached_data = self.redis.get(redis_key)

        if not cached_data:
            return None

        try:
            data = json.loads(cached_data)
            return AnalysisStateData.from_dict(data)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse cached analysis state: {e}")
            return None

    # =========================================================================
    # RETRY MANAGEMENT
    # =========================================================================

    def retry_failed_documents(
        self,
        max_retries: int = 3,
        case_id: Optional[UUID] = None
    ) -> List[UUID]:
        """
        Find and retry failed documents

        Args:
            max_retries: Maximum retry attempts allowed
            case_id: Optional case filter

        Returns:
            List of document IDs queued for retry
        """
        retried_documents = []

        # Query PostgreSQL for failed documents
        with self.postgres.get_cursor() as cursor:
            if case_id:
                cursor.execute(
                    """
                    SELECT id FROM documents
                    WHERE status = 'failed' AND case_id = %s
                    """,
                    (case_id,)
                )
            else:
                cursor.execute(
                    "SELECT id FROM documents WHERE status = 'failed'"
                )

            failed_docs = cursor.fetchall()

        for doc in failed_docs:
            document_id = doc['id']

            # Check retry count
            state_data = self.get_document_state(document_id)
            if state_data and state_data.retry_count >= max_retries:
                logger.warning(f"Document {document_id} exceeded max retries ({max_retries})")
                continue

            # Reset state to pending
            try:
                retry_count = (state_data.retry_count + 1) if state_data else 1

                # Update retry count in metadata
                metadata = state_data.metadata.copy() if state_data else {}
                metadata['retry_count'] = retry_count
                metadata['last_retry_at'] = datetime.now().isoformat()

                # Create new state with incremented retry count
                state_data = DocumentStateData(
                    document_id=str(document_id),
                    state=DocumentState.PENDING,
                    progress_percent=0.0,
                    current_stage="pending",
                    started_at=datetime.now(),
                    updated_at=datetime.now(),
                    retry_count=retry_count,
                    metadata=metadata
                )

                # Store in Redis
                redis_key = self.KEY_DOCUMENT_STATE.format(document_id=str(document_id))
                self.redis.setex(
                    redis_key,
                    self.TTL_DOCUMENT_STATE,
                    json.dumps(state_data.to_dict())
                )

                # Update PostgreSQL
                self.postgres.update_document_status(document_id, 'pending')

                retried_documents.append(document_id)
                logger.info(f"Document {document_id} queued for retry (attempt {retry_count}/{max_retries})")

            except Exception as e:
                logger.error(f"Failed to retry document {document_id}: {e}")

        logger.info(f"Retried {len(retried_documents)} failed documents")
        return retried_documents

    # =========================================================================
    # STATISTICS AND MONITORING
    # =========================================================================

    def get_processing_stats(
        self,
        case_id: Optional[UUID] = None
    ) -> ProcessingStats:
        """
        Get processing statistics

        Args:
            case_id: Optional case filter

        Returns:
            ProcessingStats with counts and metrics
        """
        with self.postgres.get_cursor() as cursor:
            # Count documents by state
            if case_id:
                cursor.execute(
                    """
                    SELECT
                        COUNT(*) as total,
                        COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
                        COUNT(CASE WHEN status = 'extracting' THEN 1 END) as extracting,
                        COUNT(CASE WHEN status = 'chunking' THEN 1 END) as chunking,
                        COUNT(CASE WHEN status = 'embedding' THEN 1 END) as embedding,
                        COUNT(CASE WHEN status = 'storing' THEN 1 END) as storing,
                        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                        AVG(EXTRACT(EPOCH FROM (processing_completed_at - processing_started_at))) as avg_time
                    FROM documents
                    WHERE case_id = %s
                    """,
                    (str(case_id),)
                )
            else:
                cursor.execute(
                    """
                    SELECT
                        COUNT(*) as total,
                        COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
                        COUNT(CASE WHEN status = 'extracting' THEN 1 END) as extracting,
                        COUNT(CASE WHEN status = 'chunking' THEN 1 END) as chunking,
                        COUNT(CASE WHEN status = 'embedding' THEN 1 END) as embedding,
                        COUNT(CASE WHEN status = 'storing' THEN 1 END) as storing,
                        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                        AVG(EXTRACT(EPOCH FROM (processing_completed_at - processing_started_at))) as avg_time
                    FROM documents
                    """
                )

            result = cursor.fetchone()

        total = result['total'] or 0
        completed = result['completed'] or 0
        failed = result['failed'] or 0

        # Calculate rates
        success_rate = (completed / total * 100) if total > 0 else 0.0
        error_rate = (failed / total * 100) if total > 0 else 0.0

        # Get error counts by type (from Redis counters)
        errors_by_type = self._get_error_counts()

        return ProcessingStats(
            total_documents=total,
            pending=result['pending'] or 0,
            extracting=result['extracting'] or 0,
            chunking=result['chunking'] or 0,
            embedding=result['embedding'] or 0,
            storing=result['storing'] or 0,
            completed=completed,
            failed=failed,
            success_rate=success_rate,
            avg_processing_time_seconds=result['avg_time'],
            error_rate=error_rate,
            errors_by_type=errors_by_type,
            case_id=str(case_id) if case_id else None
        )

    def _get_error_counts(self) -> Dict[str, int]:
        """Get error counts by type from Redis"""
        error_types = [
            "extraction_error",
            "chunking_error",
            "embedding_error",
            "storage_error",
            "timeout_error",
            "validation_error"
        ]

        errors = {}
        for error_type in error_types:
            key = self.KEY_ERROR_COUNT.format(error_type=error_type)
            count_str = self.redis.get(key)
            errors[error_type] = int(count_str) if count_str else 0

        return errors

    def increment_error_count(self, error_type: str) -> None:
        """
        Increment error counter for monitoring

        Args:
            error_type: Type of error (extraction_error, timeout_error, etc)
        """
        key = self.KEY_ERROR_COUNT.format(error_type=error_type)
        count = self.redis.increment(key)

        # Set TTL on first increment
        if count == 1:
            self.redis.client.expire(self.redis._make_key(key), 86400)  # 24 hours

        # Alert if error rate is high
        if count > 10:
            self._emit_alert(
                alert_type="high_error_rate",
                entity_id=error_type,
                message=f"High error rate detected: {error_type} (count: {count})",
                severity="warning"
            )

    # =========================================================================
    # CLEANUP
    # =========================================================================

    def cleanup_old_state(self, days: int = 7) -> int:
        """
        Clean up old state entries from Redis

        Args:
            days: Remove entries older than N days

        Returns:
            Number of entries removed
        """
        # Redis keys with TTL will auto-expire, but we can manually clean up
        # entries that should be archived to PostgreSQL

        cutoff_date = datetime.now() - timedelta(days=days)
        removed_count = 0

        # This is a simplified version - in production, you'd want to scan
        # Redis keys and check timestamps, then archive important data

        logger.info(f"Cleaned up {removed_count} old state entries (older than {days} days)")
        return removed_count

    # =========================================================================
    # INTERNAL HELPERS
    # =========================================================================

    def _is_valid_document_transition(
        self,
        current: DocumentState,
        new: DocumentState
    ) -> bool:
        """Check if state transition is valid"""
        valid_next_states = DOCUMENT_STATE_TRANSITIONS.get(current, [])
        return new in valid_next_states

    def _is_valid_analysis_transition(
        self,
        current: AnalysisState,
        new: AnalysisState
    ) -> bool:
        """Check if state transition is valid"""
        valid_next_states = ANALYSIS_STATE_TRANSITIONS.get(current, [])
        return new in valid_next_states

    def _emit_state_change_event(
        self,
        entity_type: str,
        entity_id: str,
        old_state: str,
        new_state: str,
        metadata: Dict[str, Any]
    ) -> None:
        """
        Emit state change event via Redis pub/sub

        Args:
            entity_type: "document" or "analysis"
            entity_id: Entity identifier
            old_state: Previous state
            new_state: New state
            metadata: Additional metadata
        """
        event = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "old_state": old_state,
            "new_state": new_state,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata
        }

        try:
            if self.redis.client:
                self.redis.client.publish(
                    self.CHANNEL_STATE_CHANGES,
                    json.dumps(event)
                )
                logger.debug(f"State change event emitted: {entity_type}:{entity_id} {old_state}->{new_state}")
        except Exception as e:
            logger.error(f"Failed to emit state change event: {e}")

    def _emit_alert(
        self,
        alert_type: str,
        entity_id: str,
        message: str,
        severity: Literal["info", "warning", "error", "critical"]
    ) -> None:
        """
        Emit alert via Redis pub/sub

        Args:
            alert_type: Type of alert
            entity_id: Related entity ID
            message: Alert message
            severity: Alert severity level
        """
        alert = {
            "alert_type": alert_type,
            "entity_id": entity_id,
            "message": message,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        }

        try:
            if self.redis.client:
                self.redis.client.publish(
                    self.CHANNEL_ALERTS,
                    json.dumps(alert)
                )
                logger.info(f"Alert emitted: [{severity}] {alert_type} - {message}")
        except Exception as e:
            logger.error(f"Failed to emit alert: {e}")

    def _start_timing(self, entity_id: str, operation: str) -> None:
        """Start timing an operation"""
        key = self.KEY_DOCUMENT_TIMING.format(document_id=f"{entity_id}:{operation}")
        timing_data = {
            "started_at": datetime.now().isoformat(),
            "operation": operation
        }
        self.redis.setex(key, self.TTL_TIMING_DATA, json.dumps(timing_data))

    def _end_timing(self, entity_id: str, operation: str) -> Optional[float]:
        """
        End timing an operation and return duration

        Returns:
            Duration in seconds, or None if timing wasn't started
        """
        key = self.KEY_DOCUMENT_TIMING.format(document_id=f"{entity_id}:{operation}")
        timing_json = self.redis.get(key)

        if not timing_json:
            return None

        try:
            timing_data = json.loads(timing_json)
            started_at = datetime.fromisoformat(timing_data['started_at'])
            duration = (datetime.now() - started_at).total_seconds()

            # Clean up timing key
            self.redis.delete(key)

            logger.info(f"{operation} for {entity_id} completed in {duration:.2f}s")
            return duration

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to calculate timing: {e}")
            return None

    # =========================================================================
    # MONITORING SUBSCRIPTIONS
    # =========================================================================

    def subscribe_to_state_changes(self, callback):
        """
        Subscribe to state change events

        Args:
            callback: Function to call with event data

        Example:
            def on_state_change(event):
                print(f"State changed: {event}")

            state_manager.subscribe_to_state_changes(on_state_change)
        """
        if not self.redis.client:
            logger.warning("Cannot subscribe: Redis not available")
            return

        pubsub = self.redis.client.pubsub()
        pubsub.subscribe(self.CHANNEL_STATE_CHANGES)

        logger.info("Subscribed to state change events")

        for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    event = json.loads(message['data'])
                    callback(event)
                except Exception as e:
                    logger.error(f"Error processing state change event: {e}")

    def subscribe_to_alerts(self, callback):
        """
        Subscribe to alert events

        Args:
            callback: Function to call with alert data

        Example:
            def on_alert(alert):
                print(f"Alert: {alert['severity']} - {alert['message']}")

            state_manager.subscribe_to_alerts(on_alert)
        """
        if not self.redis.client:
            logger.warning("Cannot subscribe: Redis not available")
            return

        pubsub = self.redis.client.pubsub()
        pubsub.subscribe(self.CHANNEL_ALERTS)

        logger.info("Subscribed to alert events")

        for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    alert = json.loads(message['data'])
                    callback(alert)
                except Exception as e:
                    logger.error(f"Error processing alert event: {e}")

    # =========================================================================
    # CONTEXT MANAGER
    # =========================================================================

    def close(self):
        """Close connections"""
        if self.redis:
            self.redis.close()
        if self.postgres:
            self.postgres.close()
        logger.info("StateManager closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
