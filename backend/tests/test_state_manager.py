"""
Unit Tests for StateManager
Tests state transitions, error handling, retry logic, and monitoring
"""

import pytest
import json
from uuid import uuid4
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

from src.orchestration.state_manager import (
    StateManager,
    DocumentState,
    AnalysisState,
    DocumentStateData,
    AnalysisStateData,
    ProcessingStats,
    DOCUMENT_STATE_TRANSITIONS,
    ANALYSIS_STATE_TRANSITIONS
)


# =========================================================================
# FIXTURES
# =========================================================================

@pytest.fixture
def mock_redis():
    """Mock Redis store"""
    redis = Mock()
    redis.client = Mock()
    redis.setex = Mock(return_value=True)
    redis.get = Mock(return_value=None)
    redis.delete = Mock(return_value=True)
    redis.increment = Mock(return_value=1)
    redis._make_key = Mock(side_effect=lambda x: f"investigation:{x}")
    return redis


@pytest.fixture
def mock_postgres():
    """Mock PostgreSQL store"""
    postgres = Mock()
    postgres.update_document_status = Mock(return_value=True)
    postgres.get_document = Mock(return_value=None)
    postgres.get_cursor = MagicMock()
    return postgres


@pytest.fixture
def state_manager(mock_redis, mock_postgres):
    """Create StateManager with mocked dependencies"""
    return StateManager(redis_store=mock_redis, postgres_store=mock_postgres)


# =========================================================================
# STATE TRANSITION TESTS
# =========================================================================

def test_valid_document_state_transition(state_manager, mock_redis, mock_postgres):
    """Test valid document state transitions"""
    document_id = uuid4()

    # PENDING -> EXTRACTING (valid)
    state_manager.set_document_state(
        document_id=document_id,
        state=DocumentState.PENDING
    )

    state_manager.set_document_state(
        document_id=document_id,
        state=DocumentState.EXTRACTING
    )

    # Verify Redis was called
    assert mock_redis.setex.call_count == 2


def test_invalid_document_state_transition(state_manager):
    """Test invalid document state transitions raise ValueError"""
    document_id = uuid4()

    # Set initial state
    state_manager.set_document_state(
        document_id=document_id,
        state=DocumentState.PENDING
    )

    # Try invalid transition: PENDING -> COMPLETED (should skip intermediate steps)
    with pytest.raises(ValueError, match="Invalid state transition"):
        state_manager.set_document_state(
            document_id=document_id,
            state=DocumentState.COMPLETED
        )


def test_document_state_progression(state_manager, mock_redis):
    """Test full document processing state progression"""
    document_id = uuid4()

    states = [
        DocumentState.PENDING,
        DocumentState.EXTRACTING,
        DocumentState.CHUNKING,
        DocumentState.EMBEDDING,
        DocumentState.STORING,
        DocumentState.COMPLETED
    ]

    for state in states:
        state_manager.set_document_state(
            document_id=document_id,
            state=state
        )

    # Verify all states were set
    assert mock_redis.setex.call_count == len(states)


def test_analysis_state_progression(state_manager, mock_redis):
    """Test full analysis workflow state progression"""
    analysis_id = str(uuid4())
    case_id = uuid4()

    states = [
        AnalysisState.QUEUED,
        AnalysisState.SEARCHING,
        AnalysisState.CALCULATING,
        AnalysisState.CLASSIFYING,
        AnalysisState.COMPLETED
    ]

    for state in states:
        state_manager.set_analysis_state(
            analysis_id=analysis_id,
            case_id=case_id,
            state=state
        )

    assert mock_redis.setex.call_count == len(states)


# =========================================================================
# ERROR HANDLING TESTS
# =========================================================================

def test_document_failure_state(state_manager, mock_redis):
    """Test setting document to failed state"""
    document_id = uuid4()

    state_manager.set_document_state(
        document_id=document_id,
        state=DocumentState.PENDING
    )

    # Fail during extraction
    state_manager.set_document_state(
        document_id=document_id,
        state=DocumentState.FAILED,
        error_details="PDF extraction failed: Corrupted file"
    )

    # Verify Redis pub/sub was called for alert
    assert mock_redis.client.publish.called


def test_error_count_increment(state_manager, mock_redis):
    """Test error counter incrementation"""
    mock_redis.increment.return_value = 5

    state_manager.increment_error_count("extraction_error")

    assert mock_redis.increment.called
    assert "extraction_error" in str(mock_redis.increment.call_args)


def test_high_error_rate_alert(state_manager, mock_redis):
    """Test alert emission on high error rate"""
    mock_redis.increment.return_value = 11  # Exceeds threshold

    state_manager.increment_error_count("timeout_error")

    # Should emit alert when count > 10
    assert mock_redis.client.publish.called


# =========================================================================
# RETRY LOGIC TESTS
# =========================================================================

def test_retry_failed_documents(state_manager, mock_postgres, mock_redis):
    """Test retry logic for failed documents"""
    failed_doc_1 = uuid4()
    failed_doc_2 = uuid4()

    # Mock PostgreSQL to return failed documents
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        {'id': failed_doc_1},
        {'id': failed_doc_2}
    ]
    mock_postgres.get_cursor.return_value.__enter__.return_value = mock_cursor

    # Mock get_document_state to return failed state with retry count
    def mock_get_state(doc_id):
        return DocumentStateData(
            document_id=str(doc_id),
            state=DocumentState.FAILED,
            progress_percent=0,
            current_stage="failed",
            started_at=datetime.now(),
            updated_at=datetime.now(),
            retry_count=1
        )

    state_manager.get_document_state = Mock(side_effect=mock_get_state)

    # Retry failed documents
    retried = state_manager.retry_failed_documents(max_retries=3)

    assert len(retried) == 2
    assert failed_doc_1 in retried
    assert failed_doc_2 in retried


def test_retry_respects_max_retries(state_manager, mock_postgres):
    """Test that documents exceeding max retries are not retried"""
    failed_doc = uuid4()

    # Mock PostgreSQL
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [{'id': failed_doc}]
    mock_postgres.get_cursor.return_value.__enter__.return_value = mock_cursor

    # Mock state with high retry count
    state_manager.get_document_state = Mock(return_value=DocumentStateData(
        document_id=str(failed_doc),
        state=DocumentState.FAILED,
        progress_percent=0,
        current_stage="failed",
        started_at=datetime.now(),
        updated_at=datetime.now(),
        retry_count=5  # Already exceeded max
    ))

    # Retry with max=3
    retried = state_manager.retry_failed_documents(max_retries=3)

    assert len(retried) == 0  # Should not retry


# =========================================================================
# STATE RETRIEVAL TESTS
# =========================================================================

def test_get_document_state_from_redis(state_manager, mock_redis):
    """Test retrieving document state from Redis cache"""
    document_id = uuid4()

    state_data = DocumentStateData(
        document_id=str(document_id),
        state=DocumentState.CHUNKING,
        progress_percent=50,
        current_stage="chunking",
        started_at=datetime.now(),
        updated_at=datetime.now()
    )

    mock_redis.get.return_value = json.dumps(state_data.to_dict())

    result = state_manager.get_document_state(document_id)

    assert result is not None
    assert result.state == DocumentState.CHUNKING
    assert result.progress_percent == 50


def test_get_document_state_fallback_to_postgres(state_manager, mock_redis, mock_postgres):
    """Test fallback to PostgreSQL when Redis cache misses"""
    document_id = uuid4()

    # Redis returns None (cache miss)
    mock_redis.get.return_value = None

    # PostgreSQL returns document
    mock_postgres.get_document.return_value = {
        'id': document_id,
        'status': 'completed',
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
        'metadata': {}
    }

    result = state_manager.get_document_state(document_id)

    assert result is not None
    assert result.state == DocumentState.COMPLETED
    # Should cache the result
    assert mock_redis.setex.called


def test_get_analysis_state(state_manager, mock_redis):
    """Test retrieving analysis state"""
    analysis_id = str(uuid4())

    state_data = AnalysisStateData(
        analysis_id=analysis_id,
        case_id=str(uuid4()),
        state=AnalysisState.CALCULATING,
        progress_percent=60,
        current_stage="calculating",
        started_at=datetime.now(),
        updated_at=datetime.now(),
        results=None
    )

    mock_redis.get.return_value = json.dumps(state_data.to_dict())

    result = state_manager.get_analysis_state(analysis_id)

    assert result is not None
    assert result.state == AnalysisState.CALCULATING
    assert result.progress_percent == 60


# =========================================================================
# STATISTICS TESTS
# =========================================================================

def test_get_processing_stats(state_manager, mock_postgres):
    """Test getting processing statistics"""
    # Mock database query result
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = {
        'total': 100,
        'pending': 10,
        'extracting': 5,
        'chunking': 5,
        'embedding': 5,
        'storing': 5,
        'completed': 65,
        'failed': 5,
        'avg_time': 45.5
    }
    mock_postgres.get_cursor.return_value.__enter__.return_value = mock_cursor

    stats = state_manager.get_processing_stats()

    assert stats.total_documents == 100
    assert stats.completed == 65
    assert stats.failed == 5
    assert stats.success_rate == 65.0
    assert stats.error_rate == 5.0
    assert stats.avg_processing_time_seconds == 45.5


def test_get_processing_stats_by_case(state_manager, mock_postgres):
    """Test getting statistics filtered by case"""
    case_id = uuid4()

    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = {
        'total': 20,
        'pending': 2,
        'extracting': 1,
        'chunking': 1,
        'embedding': 1,
        'storing': 1,
        'completed': 12,
        'failed': 2,
        'avg_time': 30.0
    }
    mock_postgres.get_cursor.return_value.__enter__.return_value = mock_cursor

    stats = state_manager.get_processing_stats(case_id=case_id)

    assert stats.total_documents == 20
    assert stats.case_id == str(case_id)


# =========================================================================
# EVENT EMISSION TESTS
# =========================================================================

def test_state_change_event_emission(state_manager, mock_redis):
    """Test that state changes emit events"""
    document_id = uuid4()

    # Set initial state
    state_manager.set_document_state(
        document_id=document_id,
        state=DocumentState.PENDING
    )

    # Change state
    state_manager.set_document_state(
        document_id=document_id,
        state=DocumentState.EXTRACTING
    )

    # Should publish state change event
    assert mock_redis.client.publish.called
    call_args = mock_redis.client.publish.call_args
    assert call_args[0][0] == "state_changes"


def test_alert_emission_on_failure(state_manager, mock_redis):
    """Test alert emission when document fails"""
    document_id = uuid4()

    state_manager.set_document_state(
        document_id=document_id,
        state=DocumentState.PENDING
    )

    state_manager.set_document_state(
        document_id=document_id,
        state=DocumentState.FAILED,
        error_details="Test error"
    )

    # Should publish alert
    assert mock_redis.client.publish.called
    call_args_list = mock_redis.client.publish.call_args_list

    # Check if alert channel was used
    alert_published = any(
        call[0][0] == "state_alerts"
        for call in call_args_list
    )
    assert alert_published


# =========================================================================
# DATA CLASS TESTS
# =========================================================================

def test_document_state_data_serialization():
    """Test DocumentStateData to_dict and from_dict"""
    data = DocumentStateData(
        document_id="test-123",
        state=DocumentState.EMBEDDING,
        progress_percent=75.5,
        current_stage="embedding",
        started_at=datetime.now(),
        updated_at=datetime.now(),
        retry_count=2,
        metadata={"key": "value"}
    )

    # Serialize
    dict_data = data.to_dict()
    assert dict_data['state'] == 'embedding'
    assert dict_data['progress_percent'] == 75.5

    # Deserialize
    restored = DocumentStateData.from_dict(dict_data)
    assert restored.state == DocumentState.EMBEDDING
    assert restored.progress_percent == 75.5
    assert restored.retry_count == 2


def test_analysis_state_data_serialization():
    """Test AnalysisStateData to_dict and from_dict"""
    data = AnalysisStateData(
        analysis_id="analysis-123",
        case_id="case-456",
        state=AnalysisState.CLASSIFYING,
        progress_percent=80,
        current_stage="classifying",
        started_at=datetime.now(),
        updated_at=datetime.now(),
        results={"score": 8.5}
    )

    dict_data = data.to_dict()
    assert dict_data['state'] == 'classifying'

    restored = AnalysisStateData.from_dict(dict_data)
    assert restored.state == AnalysisState.CLASSIFYING
    assert restored.results['score'] == 8.5


# =========================================================================
# TIMING TESTS
# =========================================================================

def test_timing_tracking(state_manager, mock_redis):
    """Test operation timing tracking"""
    document_id = uuid4()

    # Start timing (PENDING state)
    state_manager.set_document_state(
        document_id=document_id,
        state=DocumentState.PENDING
    )

    # Should store start time
    timing_calls = [call for call in mock_redis.setex.call_args_list
                   if 'timing' in str(call)]
    assert len(timing_calls) > 0


# =========================================================================
# CONTEXT MANAGER TESTS
# =========================================================================

def test_context_manager(mock_redis, mock_postgres):
    """Test StateManager as context manager"""
    with StateManager(redis_store=mock_redis, postgres_store=mock_postgres) as sm:
        assert sm is not None
        assert sm.redis == mock_redis
        assert sm.postgres == mock_postgres

    # Should close connections
    assert mock_redis.close.called
    assert mock_postgres.close.called


# =========================================================================
# INTEGRATION TESTS
# =========================================================================

def test_full_document_lifecycle(state_manager, mock_redis, mock_postgres):
    """Test complete document processing lifecycle"""
    document_id = uuid4()

    # Full progression
    states = [
        (DocumentState.PENDING, 0),
        (DocumentState.EXTRACTING, 20),
        (DocumentState.CHUNKING, 40),
        (DocumentState.EMBEDDING, 60),
        (DocumentState.STORING, 80),
        (DocumentState.COMPLETED, 100)
    ]

    for state, progress in states:
        state_manager.set_document_state(
            document_id=document_id,
            state=state,
            progress_percent=progress
        )

    # Verify all states were set
    assert mock_redis.setex.call_count == len(states)
    assert mock_postgres.update_document_status.call_count == len(states)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
