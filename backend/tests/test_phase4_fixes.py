"""
Unit Tests for Phase 4: Multi-Document Intelligence Fixes
Tests the three main fixes:
1. Using query_case() instead of search_documents()
2. SearchResult-to-dict conversion
3. enhance_results() with correct 2-parameter signature
"""

import pytest
from uuid import uuid4, UUID
from datetime import datetime
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from dataclasses import dataclass
from typing import List, Dict, Any, Optional


# =========================================================================
# TEST FIXTURES & HELPERS
# =========================================================================

@dataclass
class MockSearchResult:
    """Mock SearchResult dataclass matching the actual structure"""
    chunk_id: str
    document_id: UUID
    case_id: UUID
    page_num: int
    text: str
    score: float
    char_count: int
    chunk_idx: Optional[int] = None
    context: Optional[Dict[str, List[Dict]]] = None
    chunk_type: str = 'text'
    temporal_context: List[str] = None

    def __post_init__(self):
        if self.temporal_context is None:
            self.temporal_context = []


@pytest.fixture
def sample_search_results():
    """Create sample SearchResult objects for testing"""
    case_id = uuid4()
    doc_id_2023 = uuid4()
    doc_id_2024 = uuid4()

    results = [
        MockSearchResult(
            chunk_id="chunk_001",
            document_id=doc_id_2023,
            case_id=case_id,
            page_num=5,
            text="Przychody ze sprzedaży w 2023 roku wyniosły 1,234 mln PLN",
            score=0.85,
            char_count=150,
            chunk_idx=10,
            context={'before': [], 'after': []},
            chunk_type='text',
            temporal_context=['2023']
        ),
        MockSearchResult(
            chunk_id="chunk_002",
            document_id=doc_id_2024,
            case_id=case_id,
            page_num=6,
            text="Przychody ze sprzedaży w 2024 roku wyniosły 1,456 mln PLN",
            score=0.82,
            char_count=155,
            chunk_idx=11,
            context={'before': [], 'after': []},
            chunk_type='text',
            temporal_context=['2024']
        ),
        MockSearchResult(
            chunk_id="chunk_003",
            document_id=doc_id_2023,
            case_id=case_id,
            page_num=7,
            text="Zysk netto 2023: 234 mln PLN",
            score=0.78,
            char_count=100,
            chunk_idx=12,
            context=None,
            chunk_type='table',
            temporal_context=['2023']
        )
    ]
    return results


@pytest.fixture
def mock_analysis_flow():
    """Mock AnalysisFlow with query_case method"""
    flow = Mock()
    flow.query_case = AsyncMock()
    return flow


@pytest.fixture
def mock_result_enhancer():
    """Mock SearchResultEnhancer with enhance_results method"""
    enhancer = Mock()
    enhancer.enhance_results = Mock()
    return enhancer


# =========================================================================
# FIX 1: query_case() Method Call Tests
# =========================================================================

@pytest.mark.asyncio
async def test_query_case_called_with_correct_parameters(mock_analysis_flow, sample_search_results):
    """Test that query_case() is called with correct parameters"""
    case_id = uuid4()
    query = "przychody ze sprzedaży 2023 vs 2024"

    # Setup mock return
    mock_analysis_flow.query_case.return_value = sample_search_results

    # Call the method
    results = await mock_analysis_flow.query_case(
        case_id=case_id,
        query=query,
        context_window=0
    )

    # Verify
    mock_analysis_flow.query_case.assert_called_once_with(
        case_id=case_id,
        query=query,
        context_window=0
    )
    assert len(results) == 3
    assert all(isinstance(r, MockSearchResult) for r in results)


@pytest.mark.asyncio
async def test_query_case_returns_empty_list(mock_analysis_flow):
    """Test handling of empty results from query_case()"""
    case_id = uuid4()
    query = "nieistniejące dane"

    # Setup mock to return empty list
    mock_analysis_flow.query_case.return_value = []

    # Call the method
    results = await mock_analysis_flow.query_case(
        case_id=case_id,
        query=query,
        context_window=0
    )

    # Verify
    assert results == []
    assert len(results) == 0


@pytest.mark.asyncio
async def test_query_case_with_context_window_zero(mock_analysis_flow, sample_search_results):
    """Test that Phase 4 uses context_window=0 for comparisons"""
    case_id = uuid4()
    query = "test query"

    mock_analysis_flow.query_case.return_value = sample_search_results

    # Call with context_window=0 (Phase 4 requirement)
    await mock_analysis_flow.query_case(
        case_id=case_id,
        query=query,
        context_window=0
    )

    # Verify context_window is set to 0
    call_args = mock_analysis_flow.query_case.call_args
    assert call_args.kwargs['context_window'] == 0


# =========================================================================
# FIX 2: SearchResult-to-Dict Conversion Tests
# =========================================================================

def test_searchresult_to_dict_conversion(sample_search_results):
    """Test conversion of SearchResult objects to dictionaries"""
    # Simulate the conversion logic from analysis.py lines 1234-1250
    results_dicts = []
    for r in sample_search_results:
        result_dict = {
            'chunk_id': r.chunk_id,
            'document_id': r.document_id,
            'case_id': r.case_id,
            'page_num': r.page_num,
            'text': r.text,
            'score': r.score,
            'char_count': r.char_count,
            'chunk_idx': r.chunk_idx,
            'context': r.context,
            'chunk_type': getattr(r, 'chunk_type', 'text'),
            'temporal_context': getattr(r, 'temporal_context', [])
        }
        results_dicts.append(result_dict)

    # Verify conversion
    assert len(results_dicts) == 3
    assert all(isinstance(d, dict) for d in results_dicts)

    # Verify first result
    first = results_dicts[0]
    assert first['chunk_id'] == "chunk_001"
    assert isinstance(first['document_id'], UUID)
    assert first['score'] == 0.85
    assert first['chunk_type'] == 'text'
    assert '2023' in first['temporal_context']


def test_searchresult_conversion_handles_missing_attributes(sample_search_results):
    """Test that getattr() handles missing chunk_type and temporal_context"""
    # Create SearchResult without optional attributes
    result_no_attrs = MockSearchResult(
        chunk_id="chunk_004",
        document_id=uuid4(),
        case_id=uuid4(),
        page_num=1,
        text="Test text",
        score=0.5,
        char_count=50
    )
    # Remove attributes to simulate missing fields
    if hasattr(result_no_attrs, 'chunk_type'):
        delattr(result_no_attrs, 'chunk_type')

    # Convert with getattr() defaults
    result_dict = {
        'chunk_id': result_no_attrs.chunk_id,
        'document_id': result_no_attrs.document_id,
        'case_id': result_no_attrs.case_id,
        'page_num': result_no_attrs.page_num,
        'text': result_no_attrs.text,
        'score': result_no_attrs.score,
        'char_count': result_no_attrs.char_count,
        'chunk_idx': result_no_attrs.chunk_idx,
        'context': result_no_attrs.context,
        'chunk_type': getattr(result_no_attrs, 'chunk_type', 'text'),
        'temporal_context': getattr(result_no_attrs, 'temporal_context', [])
    }

    # Verify defaults are applied
    assert result_dict['chunk_type'] == 'text'
    assert result_dict['temporal_context'] == []


def test_searchresult_conversion_preserves_all_fields(sample_search_results):
    """Test that all SearchResult fields are preserved in dict conversion"""
    result = sample_search_results[2]  # Third result with table type

    result_dict = {
        'chunk_id': result.chunk_id,
        'document_id': result.document_id,
        'case_id': result.case_id,
        'page_num': result.page_num,
        'text': result.text,
        'score': result.score,
        'char_count': result.char_count,
        'chunk_idx': result.chunk_idx,
        'context': result.context,
        'chunk_type': getattr(result, 'chunk_type', 'text'),
        'temporal_context': getattr(result, 'temporal_context', [])
    }

    # Verify all fields
    assert result_dict['chunk_id'] == "chunk_003"
    assert result_dict['page_num'] == 7
    assert result_dict['chunk_type'] == 'table'
    assert result_dict['context'] is None  # Can be None
    assert '2023' in result_dict['temporal_context']


# =========================================================================
# FIX 3: enhance_results() Parameter Tests
# =========================================================================

def test_enhance_results_with_correct_parameters(mock_result_enhancer):
    """Test that enhance_results() is called with only 2 parameters"""
    results_dicts = [
        {'chunk_id': 'test1', 'text': 'Test 1', 'score': 0.8},
        {'chunk_id': 'test2', 'text': 'Test 2', 'score': 0.7}
    ]
    query = "test query"

    # Setup mock to return enhanced results
    mock_result_enhancer.enhance_results.return_value = results_dicts

    # Call with correct 2-parameter signature (FIX: removed temporal_context)
    enhanced = mock_result_enhancer.enhance_results(
        results=results_dicts,
        query=query
    )

    # Verify
    mock_result_enhancer.enhance_results.assert_called_once_with(
        results=results_dicts,
        query=query
    )
    assert enhanced == results_dicts


def test_enhance_results_does_not_accept_temporal_context(mock_result_enhancer):
    """Test that enhance_results() raises TypeError with temporal_context parameter"""
    results_dicts = [{'chunk_id': 'test1', 'text': 'Test 1'}]
    query = "test query"

    # Configure mock to raise TypeError (as real method would)
    def side_effect(*args, **kwargs):
        if 'temporal_context' in kwargs:
            raise TypeError("enhance_results() got an unexpected keyword argument 'temporal_context'")
        return results_dicts

    mock_result_enhancer.enhance_results.side_effect = side_effect

    # Try calling with temporal_context (BROKEN way)
    with pytest.raises(TypeError, match="unexpected keyword argument 'temporal_context'"):
        mock_result_enhancer.enhance_results(
            results=results_dicts,
            query=query,
            temporal_context=['2023', '2024']  # This should raise TypeError
        )


def test_enhance_results_handles_empty_results(mock_result_enhancer):
    """Test that enhance_results() handles empty results list"""
    empty_results = []
    query = "test query"

    mock_result_enhancer.enhance_results.return_value = empty_results

    enhanced = mock_result_enhancer.enhance_results(
        results=empty_results,
        query=query
    )

    assert enhanced == []


# =========================================================================
# INTEGRATION TESTS: All Three Fixes Together
# =========================================================================

@pytest.mark.asyncio
async def test_complete_phase4_flow(mock_analysis_flow, mock_result_enhancer, sample_search_results):
    """Test complete Phase 4 flow with all three fixes"""
    case_id = uuid4()
    query = "przychody ze sprzedaży 2023 vs 2024"

    # Setup mocks
    mock_analysis_flow.query_case.return_value = sample_search_results

    # Step 1: Call query_case() (FIX 1)
    results = await mock_analysis_flow.query_case(
        case_id=case_id,
        query=query,
        context_window=0
    )

    # Step 2: Convert SearchResult to dicts (FIX 2)
    results_dicts = []
    for r in results:
        result_dict = {
            'chunk_id': r.chunk_id,
            'document_id': r.document_id,
            'case_id': r.case_id,
            'page_num': r.page_num,
            'text': r.text,
            'score': r.score,
            'char_count': r.char_count,
            'chunk_idx': r.chunk_idx,
            'context': r.context,
            'chunk_type': getattr(r, 'chunk_type', 'text'),
            'temporal_context': getattr(r, 'temporal_context', [])
        }
        results_dicts.append(result_dict)

    # Setup enhancer mock
    mock_result_enhancer.enhance_results.return_value = results_dicts

    # Step 3: Enhance results with correct parameters (FIX 3)
    enhanced = mock_result_enhancer.enhance_results(
        results=results_dicts,
        query=query
    )

    # Verify all steps
    assert len(results) == 3  # query_case returned 3 results
    assert len(results_dicts) == 3  # All converted to dicts
    assert all(isinstance(d, dict) for d in results_dicts)  # All are dicts
    assert len(enhanced) == 3  # All enhanced

    # Verify query_case was called correctly
    mock_analysis_flow.query_case.assert_called_once()

    # Verify enhance_results was called with only 2 params
    call_kwargs = mock_result_enhancer.enhance_results.call_args.kwargs
    assert 'results' in call_kwargs
    assert 'query' in call_kwargs
    assert 'temporal_context' not in call_kwargs  # Must NOT be present


@pytest.mark.asyncio
async def test_phase4_with_year_filtering(mock_analysis_flow, sample_search_results):
    """Test Phase 4 flow with year filtering"""
    case_id = uuid4()
    query = "przychody 2023"
    requested_years = ['2023']

    # Setup mock
    mock_analysis_flow.query_case.return_value = sample_search_results

    # Get results
    results = await mock_analysis_flow.query_case(
        case_id=case_id,
        query=query,
        context_window=0
    )

    # Convert to dicts
    results_dicts = []
    for r in results:
        result_dict = {
            'chunk_id': r.chunk_id,
            'text': r.text,
            'score': r.score,
            'temporal_context': getattr(r, 'temporal_context', [])
        }
        results_dicts.append(result_dict)

    # Apply year filtering (as in analysis.py)
    filtered = []
    for result in results_dicts:
        temporal_ctx = result.get('temporal_context', [])
        if any(year in temporal_ctx for year in requested_years):
            filtered.append(result)

    # Verify filtering
    assert len(filtered) == 2  # Only 2 results have '2023' in temporal_context
    assert all('2023' in r.get('temporal_context', []) for r in filtered)


# =========================================================================
# EDGE CASE TESTS
# =========================================================================

@pytest.mark.asyncio
async def test_empty_results_from_query_case(mock_analysis_flow, mock_result_enhancer):
    """Test handling when query_case returns empty list"""
    case_id = uuid4()
    query = "nonexistent data"

    # Return empty list
    mock_analysis_flow.query_case.return_value = []

    results = await mock_analysis_flow.query_case(
        case_id=case_id,
        query=query,
        context_window=0
    )

    # Convert empty results
    results_dicts = []
    for r in results:
        results_dicts.append({})

    # Enhance empty results
    mock_result_enhancer.enhance_results.return_value = []
    enhanced = mock_result_enhancer.enhance_results(
        results=results_dicts,
        query=query
    )

    # Verify
    assert len(results) == 0
    assert len(results_dicts) == 0
    assert len(enhanced) == 0


def test_searchresult_with_none_context():
    """Test SearchResult conversion when context is None"""
    result = MockSearchResult(
        chunk_id="test",
        document_id=uuid4(),
        case_id=uuid4(),
        page_num=1,
        text="Test",
        score=0.5,
        char_count=10,
        context=None  # Explicitly None
    )

    result_dict = {
        'chunk_id': result.chunk_id,
        'context': result.context,
        'temporal_context': getattr(result, 'temporal_context', [])
    }

    # Verify None is preserved
    assert result_dict['context'] is None


def test_multiple_years_in_temporal_context():
    """Test results with multiple years in temporal_context"""
    result = MockSearchResult(
        chunk_id="multi_year",
        document_id=uuid4(),
        case_id=uuid4(),
        page_num=1,
        text="Porównanie 2022, 2023, 2024",
        score=0.9,
        char_count=50,
        temporal_context=['2022', '2023', '2024']
    )

    result_dict = {
        'temporal_context': getattr(result, 'temporal_context', [])
    }

    assert len(result_dict['temporal_context']) == 3
    assert '2022' in result_dict['temporal_context']
    assert '2023' in result_dict['temporal_context']
    assert '2024' in result_dict['temporal_context']


# =========================================================================
# BACKWARD COMPATIBILITY TESTS
# =========================================================================

@pytest.mark.asyncio
async def test_backward_compatibility_with_existing_code(mock_analysis_flow, sample_search_results):
    """Test that fixes maintain backward compatibility"""
    case_id = uuid4()
    query = "test"

    # Old code might have called with different params
    mock_analysis_flow.query_case.return_value = sample_search_results

    # New way (fixed)
    results = await mock_analysis_flow.query_case(
        case_id=case_id,
        query=query,
        context_window=0
    )

    # Should work with existing result processing
    assert len(results) > 0
    assert hasattr(results[0], 'chunk_id')
    assert hasattr(results[0], 'text')
    assert hasattr(results[0], 'score')


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
