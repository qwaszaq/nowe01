# E5 Embeddings Testing Guide

## Overview

This guide provides testing recommendations for the E5-large embeddings pipeline integrated with LM Studio and Qdrant.

## Prerequisites

1. **LM Studio Running**
   - Endpoint: `http://192.168.200.226:1234/v1`
   - Model loaded: `intfloat/multilingual-e5-large`
   - Embeddings API enabled

2. **Qdrant Running**
   - Host: `localhost`
   - Port: `6333`
   - Collection created: `document_chunks`

3. **Dependencies Installed**
   ```bash
   pip install -r requirements.txt
   ```

## Testing Levels

### 1. Unit Tests

Test individual E5Embeddings methods in isolation.

**Test File**: `tests/test_e5_embeddings.py`

```python
import pytest
from src.core.embeddings import E5Embeddings

@pytest.mark.asyncio
async def test_embed_query():
    """Test query embedding with 'query:' prefix"""
    embeddings = E5Embeddings()

    query = "What is the company's revenue?"
    vector = await embeddings.embed_query(query)

    assert len(vector) == 1024
    assert all(isinstance(v, float) for v in vector)
    await embeddings.close()

@pytest.mark.asyncio
async def test_embed_chunks():
    """Test batch chunk embedding with 'passage:' prefix"""
    embeddings = E5Embeddings()

    chunks = [
        {"text": "Revenue increased by 15%"},
        {"text": "Profit margin improved to 8.2%"}
    ]

    vectors = await embeddings.embed_chunks(chunks, batch_size=2)

    assert len(vectors) == 2
    assert all(len(v) == 1024 for v in vectors)
    await embeddings.close()

@pytest.mark.asyncio
async def test_preprocessing():
    """Test text preprocessing with prefixes"""
    embeddings = E5Embeddings()

    query_text = embeddings._preprocess_text("test", prefix="query")
    assert query_text == "query: test"

    passage_text = embeddings._preprocess_text("test", prefix="passage")
    assert passage_text == "passage: test"

    await embeddings.close()

@pytest.mark.asyncio
async def test_batch_sizes():
    """Test different batch sizes"""
    embeddings = E5Embeddings()

    chunks = [{"text": f"Chunk {i}"} for i in range(100)]

    for batch_size in [1, 10, 32, 64]:
        vectors = await embeddings.embed_chunks(chunks, batch_size=batch_size)
        assert len(vectors) == 100

    await embeddings.close()

@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling for invalid inputs"""
    embeddings = E5Embeddings(endpoint="http://invalid:9999")

    with pytest.raises(Exception):
        await embeddings.embed_query("test")

    await embeddings.close()

@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint"""
    embeddings = E5Embeddings()

    health = await embeddings.health_check()

    assert health["status"] == "healthy"
    assert health["dimensions"] == 1024
    await embeddings.close()
```

### 2. Integration Tests

Test integration with QdrantStore and TextChunker.

**Test File**: `tests/test_embeddings_integration.py`

```python
import pytest
from uuid import uuid4
from src.core.embeddings import E5Embeddings
from src.storage.qdrant_store import QdrantStore
from src.core.extractors.text_chunker import TextChunker

@pytest.mark.asyncio
async def test_end_to_end_pipeline():
    """Test full pipeline: chunk -> embed -> store -> search"""
    # Setup
    embeddings = E5Embeddings()
    qdrant = QdrantStore()
    chunker = TextChunker(chunk_size=750, overlap=120)

    # Create sample pages
    pages = [
        {"page_num": 1, "text": "Company revenue is $10M with 15% growth."},
        {"page_num": 2, "text": "Net profit margin improved to 8.2%."}
    ]

    # Chunk
    chunks = chunker.chunk_pages(pages)
    assert len(chunks) == 2

    # Embed
    vectors = await embeddings.embed_chunks(chunks)
    assert len(vectors) == len(chunks)

    # Store
    case_id = uuid4()
    doc_id = uuid4()
    count = qdrant.store_chunks(case_id, doc_id, chunks, vectors)
    assert count == len(chunks)

    # Search
    query = "What is the profit margin?"
    query_vec = await embeddings.embed_query(query)
    results = qdrant.search_chunks(query_vec, case_id=case_id, limit=2)

    assert len(results) > 0
    assert results[0]["score"] > 0.5

    # Cleanup
    qdrant.delete_document_chunks(doc_id)
    await embeddings.close()

@pytest.mark.asyncio
async def test_semantic_search_quality():
    """Test semantic search retrieves relevant chunks"""
    embeddings = E5Embeddings()
    qdrant = QdrantStore()

    # Create chunks with known content
    chunks = [
        {"text": "Revenue increased by 15% to $10 million", "page_num": 1, "chunk_idx": 0},
        {"text": "Operating expenses decreased by 12%", "page_num": 1, "chunk_idx": 1},
        {"text": "Net profit margin improved to 8.2%", "page_num": 2, "chunk_idx": 0}
    ]

    # Add chunk IDs
    for i, chunk in enumerate(chunks):
        chunk["chunk_id"] = f"test_chunk_{i}"
        chunk["char_count"] = len(chunk["text"])
        chunk["word_count"] = len(chunk["text"].split())

    # Embed and store
    vectors = await embeddings.embed_chunks(chunks)
    case_id = uuid4()
    doc_id = uuid4()
    qdrant.store_chunks(case_id, doc_id, chunks, vectors)

    # Test queries
    test_cases = [
        ("revenue growth", 0),  # Should match chunk 0
        ("expenses", 1),        # Should match chunk 1
        ("profitability", 2)    # Should match chunk 2
    ]

    for query, expected_idx in test_cases:
        query_vec = await embeddings.embed_query(query)
        results = qdrant.search_chunks(query_vec, case_id=case_id, limit=1)

        assert len(results) > 0
        # Check if top result is the expected chunk
        assert expected_idx in [int(r["chunk_id"].split("_")[-1]) for r in results[:1]]

    # Cleanup
    qdrant.delete_document_chunks(doc_id)
    await embeddings.close()

@pytest.mark.asyncio
async def test_large_document():
    """Test processing large document (100+ chunks)"""
    embeddings = E5Embeddings()
    qdrant = QdrantStore()

    # Generate 100 chunks
    chunks = [
        {
            "chunk_id": f"chunk_{i}",
            "text": f"Financial data for quarter {i}: Revenue ${i}M, Profit {i}%",
            "page_num": i // 10,
            "chunk_idx": i % 10,
            "char_count": 50,
            "word_count": 10
        }
        for i in range(100)
    ]

    # Embed with batch processing
    vectors = await embeddings.embed_chunks(chunks, batch_size=32)
    assert len(vectors) == 100

    # Store
    case_id = uuid4()
    doc_id = uuid4()
    count = qdrant.store_chunks(case_id, doc_id, chunks, vectors)
    assert count == 100

    # Search
    query_vec = await embeddings.embed_query("financial revenue")
    results = qdrant.search_chunks(query_vec, case_id=case_id, limit=10)
    assert len(results) == 10

    # Cleanup
    qdrant.delete_document_chunks(doc_id)
    await embeddings.close()
```

### 3. Quality Evaluation Tests

Measure retrieval quality with metrics.

**Test File**: `tests/test_retrieval_quality.py`

```python
import pytest
from typing import List, Dict
from src.core.embeddings import E5Embeddings
from src.storage.qdrant_store import QdrantStore

def calculate_precision_at_k(relevant: List[str], retrieved: List[str], k: int = 5) -> float:
    """Calculate Precision@K"""
    retrieved_k = retrieved[:k]
    relevant_retrieved = len(set(relevant) & set(retrieved_k))
    return relevant_retrieved / k if k > 0 else 0.0

def calculate_mrr(relevant: List[str], retrieved: List[str]) -> float:
    """Calculate Mean Reciprocal Rank"""
    for idx, chunk_id in enumerate(retrieved, 1):
        if chunk_id in relevant:
            return 1.0 / idx
    return 0.0

@pytest.mark.asyncio
async def test_precision_at_5():
    """Test retrieval quality: Precision@5 > 80%"""
    embeddings = E5Embeddings()
    qdrant = QdrantStore()

    # Create test dataset with known relevant chunks
    test_cases = [
        {
            "query": "company revenue",
            "relevant_chunks": ["Revenue increased by 15%", "Total revenue: $10M"],
            "irrelevant_chunks": ["Operating expenses", "Employee count", "Market share"]
        },
        {
            "query": "profitability metrics",
            "relevant_chunks": ["Net profit margin: 8.2%", "ROE: 12%"],
            "irrelevant_chunks": ["Revenue data", "Cash position", "Debt level"]
        }
    ]

    precision_scores = []

    for test_case in test_cases:
        # Setup chunks
        all_chunks = []
        relevant_ids = []

        for i, text in enumerate(test_case["relevant_chunks"]):
            chunk = {
                "chunk_id": f"relevant_{i}",
                "text": text,
                "page_num": 1,
                "chunk_idx": i,
                "char_count": len(text),
                "word_count": len(text.split())
            }
            all_chunks.append(chunk)
            relevant_ids.append(chunk["chunk_id"])

        for i, text in enumerate(test_case["irrelevant_chunks"]):
            chunk = {
                "chunk_id": f"irrelevant_{i}",
                "text": text,
                "page_num": 2,
                "chunk_idx": i,
                "char_count": len(text),
                "word_count": len(text.split())
            }
            all_chunks.append(chunk)

        # Embed and store
        vectors = await embeddings.embed_chunks(all_chunks)
        case_id = uuid4()
        doc_id = uuid4()
        qdrant.store_chunks(case_id, doc_id, all_chunks, vectors)

        # Search
        query_vec = await embeddings.embed_query(test_case["query"])
        results = qdrant.search_chunks(query_vec, case_id=case_id, limit=5)

        retrieved_ids = [r["chunk_id"] for r in results]
        precision = calculate_precision_at_k(relevant_ids, retrieved_ids, k=5)
        precision_scores.append(precision)

        # Cleanup
        qdrant.delete_document_chunks(doc_id)

    avg_precision = sum(precision_scores) / len(precision_scores)
    assert avg_precision > 0.8, f"Precision@5 = {avg_precision:.2%} (target: >80%)"

    await embeddings.close()
```

### 4. Performance Tests

Measure throughput and latency.

**Test File**: `tests/test_embeddings_performance.py`

```python
import pytest
import time
from src.core.embeddings import E5Embeddings

@pytest.mark.asyncio
async def test_embedding_speed():
    """Test embedding throughput (target: >5 chunks/sec)"""
    embeddings = E5Embeddings()

    chunks = [
        {"text": f"Sample financial text chunk number {i}" * 10}
        for i in range(100)
    ]

    start = time.time()
    vectors = await embeddings.embed_chunks(chunks, batch_size=32)
    duration = time.time() - start

    throughput = len(chunks) / duration

    assert throughput > 5.0, f"Throughput: {throughput:.2f} chunks/sec (target: >5)"
    print(f"Embedding speed: {throughput:.2f} chunks/sec")

    await embeddings.close()

@pytest.mark.asyncio
async def test_query_latency():
    """Test query embedding latency (target: <1 second)"""
    embeddings = E5Embeddings()

    query = "What is the company's financial performance?"

    start = time.time()
    vector = await embeddings.embed_query(query)
    latency = time.time() - start

    assert latency < 1.0, f"Query latency: {latency:.3f}s (target: <1s)"
    print(f"Query latency: {latency:.3f}s")

    await embeddings.close()
```

## Manual Testing

### 1. Health Check

```bash
cd backend
python -c "
import asyncio
from src.core.embeddings import E5Embeddings
from src.config import settings

async def main():
    embeddings = E5Embeddings(
        endpoint=settings.llm_endpoint,
        model=settings.embedding_model,
        dimensions=settings.embedding_dimension
    )
    health = await embeddings.health_check()
    print(health)
    await embeddings.close()

asyncio.run(main())
"
```

### 2. Run Example Usage

```bash
cd backend
python src/core/embeddings/example_usage.py
```

### 3. Test with Real Document

```bash
cd backend
python -c "
import asyncio
from uuid import uuid4
from src.core.embeddings import E5Embeddings
from src.storage.qdrant_store import QdrantStore
from src.core.extractors import PDFProcessor, TextChunker
from src.config import settings

async def main():
    # Load PDF
    processor = PDFProcessor()
    pages = processor.extract_pages('path/to/your/document.pdf')

    # Chunk
    chunker = TextChunker()
    chunks = chunker.chunk_pages(pages)

    # Embed
    embeddings = E5Embeddings()
    vectors = await embeddings.embed_chunks(chunks)

    # Store
    qdrant = QdrantStore()
    case_id = uuid4()
    doc_id = uuid4()
    qdrant.store_chunks(case_id, doc_id, chunks, vectors)

    # Search
    query = 'YOUR QUERY HERE'
    query_vec = await embeddings.embed_query(query)
    results = qdrant.search_chunks(query_vec, case_id=case_id, limit=5)

    for r in results:
        print(f\"Score: {r['score']:.3f} | {r['text'][:100]}...\")

    await embeddings.close()

asyncio.run(main())
"
```

## Success Criteria

- ✅ All unit tests pass
- ✅ Integration tests complete successfully
- ✅ Precision@5 > 80%
- ✅ Embedding speed > 5 chunks/second
- ✅ Query latency < 1 second
- ✅ Health check returns "healthy"
- ✅ No memory leaks during batch processing

## Troubleshooting

### LM Studio Connection Issues

- Check LM Studio is running: `curl http://192.168.200.226:1234/v1/models`
- Verify model loaded in LM Studio UI
- Check firewall settings

### Qdrant Connection Issues

- Check Qdrant running: `curl http://localhost:6333/collections`
- Verify collection created
- Check disk space

### Low Retrieval Quality

- Verify E5 prefixes applied correctly
- Check embedding dimensions (should be 1024)
- Review chunk size and overlap settings
- Analyze query formulation

### Slow Embedding Speed

- Increase batch size (try 64)
- Check LM Studio GPU utilization
- Monitor network latency
- Consider local LM Studio installation
