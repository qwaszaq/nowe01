# E5 Embeddings Integration Guide

## Overview

This document describes how the E5-large embeddings pipeline integrates with the Investigation Intelligence Platform's existing components.

## Architecture

```
PDF Document
    ↓
PDFProcessor (pdf_processor.py)
    ↓ pages
TextChunker (text_chunker.py)
    ↓ chunks
E5Embeddings (e5_embeddings.py)
    ↓ vectors
QdrantStore (qdrant_store.py)
    ↓ stored
Semantic Search
```

## Key Components

### 1. E5Embeddings Class

**Location**: `/backend/src/core/embeddings/e5_embeddings.py`

**Responsibilities**:
- Generate 1024-dimensional embeddings via LM Studio
- Add E5-specific prefixes ('query:' or 'passage:')
- Batch processing with progress logging
- Error handling with automatic retries

**Key Methods**:
```python
# Embed search queries
async def embed_query(query: str) -> List[float]

# Embed document chunks in batches
async def embed_chunks(chunks: List[Dict], batch_size: int = 32) -> List[List[float]]

# Check LM Studio health
async def health_check() -> Dict[str, Any]
```

**Configuration** (from `settings.py`):
```python
llm_endpoint: str = "http://192.168.200.226:1234/v1"
embedding_model: str = "intfloat/multilingual-e5-large"
embedding_dimension: int = 1024
embedding_batch_size: int = 32
```

### 2. QdrantStore Integration

**Location**: `/backend/src/storage/qdrant_store.py`

**Integration Points**:

```python
# Store embedded chunks
def store_chunks(
    case_id: UUID,
    document_id: UUID,
    chunks: List[Dict],       # From TextChunker
    embeddings: List[List[float]]  # From E5Embeddings
) -> int

# Semantic search
def search_chunks(
    query_embedding: List[float],  # From E5Embeddings.embed_query()
    case_id: Optional[UUID] = None,
    document_id: Optional[UUID] = None,
    limit: int = 10,
    score_threshold: float = 0.7
) -> List[Dict]
```

**Collection Configuration**:
- Name: `document_chunks`
- Vector size: 1024 (matches E5-large)
- Distance: Cosine
- Indexes: `case_id`, `document_id`, `page_num`

### 3. TextChunker Integration

**Location**: `/backend/src/core/extractors/text_chunker.py`

**Chunk Format** (compatible with E5Embeddings):
```python
{
    "chunk_id": str,      # Unique hash
    "text": str,          # Full chunk text (required by E5Embeddings)
    "page_num": int,      # Page number
    "chunk_idx": int,     # Index within page
    "char_count": int,    # Character count
    "word_count": int,    # Word count
    "is_complete_page": bool
}
```

**Settings**:
```python
chunk_size: int = 750      # Characters per chunk
chunk_overlap: int = 120   # Overlap between chunks
```

## End-to-End Workflow

### Document Processing Pipeline

```python
from uuid import uuid4
from src.core.extractors import PDFProcessor, TextChunker
from src.core.embeddings import E5Embeddings
from src.storage.qdrant_store import QdrantStore
from src.config import settings

async def process_document(pdf_path: str, case_id: UUID, document_id: UUID):
    """Complete document processing pipeline"""

    # Step 1: Extract pages from PDF
    processor = PDFProcessor()
    pages = processor.extract_pages(pdf_path)
    print(f"Extracted {len(pages)} pages")

    # Step 2: Chunk pages
    chunker = TextChunker(
        chunk_size=settings.chunk_size,
        overlap=settings.chunk_overlap
    )
    chunks = chunker.chunk_pages(pages)
    print(f"Created {len(chunks)} chunks")

    # Step 3: Generate embeddings
    embeddings = E5Embeddings(
        endpoint=settings.llm_endpoint,
        model=settings.embedding_model,
        dimensions=settings.embedding_dimension
    )

    try:
        vectors = await embeddings.embed_chunks(
            chunks,
            batch_size=settings.embedding_batch_size
        )
        print(f"Generated {len(vectors)} embeddings")

        # Step 4: Store in Qdrant
        qdrant = QdrantStore()
        stored_count = qdrant.store_chunks(
            case_id=case_id,
            document_id=document_id,
            chunks=chunks,
            embeddings=vectors
        )
        print(f"Stored {stored_count} chunks in Qdrant")

        return {
            "pages": len(pages),
            "chunks": len(chunks),
            "stored": stored_count
        }

    finally:
        await embeddings.close()
```

### Semantic Search

```python
async def semantic_search(
    query: str,
    case_id: UUID,
    limit: int = 10
) -> List[Dict]:
    """Search for relevant chunks"""

    embeddings = E5Embeddings(
        endpoint=settings.llm_endpoint,
        model=settings.embedding_model,
        dimensions=settings.embedding_dimension
    )

    try:
        # Embed query
        query_vector = await embeddings.embed_query(query)

        # Search Qdrant
        qdrant = QdrantStore()
        results = qdrant.search_chunks(
            query_embedding=query_vector,
            case_id=case_id,
            limit=limit,
            score_threshold=0.7
        )

        return results

    finally:
        await embeddings.close()
```

## API Endpoint Integration

### FastAPI Route Example

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from uuid import UUID

router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    case_id: UUID
    limit: int = 10
    score_threshold: float = 0.7

class SearchResult(BaseModel):
    chunk_id: str
    document_id: UUID
    page_num: int
    text: str
    score: float

@router.post("/search/semantic", response_model=List[SearchResult])
async def semantic_search_endpoint(request: SearchRequest):
    """
    Semantic search across document chunks

    Uses E5-large embeddings for similarity matching
    """
    try:
        # Initialize embeddings
        embeddings = E5Embeddings(
            endpoint=settings.llm_endpoint,
            model=settings.embedding_model,
            dimensions=settings.embedding_dimension
        )

        # Embed query
        query_vector = await embeddings.embed_query(request.query)

        # Search
        qdrant = QdrantStore()
        results = qdrant.search_chunks(
            query_embedding=query_vector,
            case_id=request.case_id,
            limit=request.limit,
            score_threshold=request.score_threshold
        )

        await embeddings.close()

        return [SearchResult(**r) for r in results]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Batch Processing Integration

### Background Task with Celery

```python
from celery import shared_task
from uuid import UUID
import asyncio

@shared_task
def process_document_task(pdf_path: str, case_id: str, document_id: str):
    """
    Celery task for async document processing

    Args:
        pdf_path: Path to PDF file
        case_id: Case UUID (as string)
        document_id: Document UUID (as string)
    """
    # Convert UUIDs
    case_uuid = UUID(case_id)
    doc_uuid = UUID(document_id)

    # Run async pipeline
    result = asyncio.run(
        process_document(pdf_path, case_uuid, doc_uuid)
    )

    return result
```

## Performance Optimization

### Connection Pooling

```python
class EmbeddingsPool:
    """Connection pool for E5Embeddings clients"""

    def __init__(self, pool_size: int = 5):
        self.pool_size = pool_size
        self.clients = []

    async def initialize(self):
        """Create pool of embeddings clients"""
        for _ in range(self.pool_size):
            client = E5Embeddings()
            self.clients.append(client)

    async def get_client(self) -> E5Embeddings:
        """Get available client from pool"""
        # Simple round-robin (can be improved with queue)
        return self.clients[0]

    async def close_all(self):
        """Close all clients in pool"""
        for client in self.clients:
            await client.close()
```

### Caching Strategy

```python
from redis import Redis
import json
import hashlib

class EmbeddingsCache:
    """Redis cache for embeddings"""

    def __init__(self, redis_client: Redis, ttl: int = 86400):
        self.redis = redis_client
        self.ttl = ttl

    def _get_key(self, text: str, prefix: str) -> str:
        """Generate cache key"""
        content = f"{prefix}:{text}"
        hash_key = hashlib.md5(content.encode()).hexdigest()
        return f"embedding:{hash_key}"

    async def get_embedding(
        self,
        text: str,
        prefix: str,
        embeddings: E5Embeddings
    ) -> List[float]:
        """Get embedding with caching"""

        # Check cache
        key = self._get_key(text, prefix)
        cached = self.redis.get(key)

        if cached:
            return json.loads(cached)

        # Generate embedding
        if prefix == "query":
            vector = await embeddings.embed_query(text)
        else:
            vectors = await embeddings.embed_chunks([{"text": text}])
            vector = vectors[0]

        # Cache result
        self.redis.setex(key, self.ttl, json.dumps(vector))

        return vector
```

## Monitoring & Metrics

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram

# Counters
embeddings_total = Counter(
    "embeddings_generated_total",
    "Total embeddings generated",
    ["type"]  # query or passage
)

embeddings_errors = Counter(
    "embeddings_errors_total",
    "Total embedding errors",
    ["error_type"]
)

# Histograms
embedding_duration = Histogram(
    "embedding_duration_seconds",
    "Time to generate embeddings",
    ["batch_size"]
)

search_duration = Histogram(
    "search_duration_seconds",
    "Time to perform semantic search"
)
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Log key events
logger.info(f"Embedded {len(chunks)} chunks in {duration:.2f}s")
logger.warning(f"Low similarity score: {score:.3f}")
logger.error(f"Embedding failed: {error}", exc_info=True)
```

## Error Handling

### Retry Strategy

The E5Embeddings class uses `tenacity` for automatic retries:

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
    reraise=True
)
async def _embed_batch(self, texts: List[str]) -> List[List[float]]:
    # API call with automatic retry
    ...
```

### Circuit Breaker Pattern

```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
async def embed_with_circuit_breaker(embeddings: E5Embeddings, text: str):
    """
    Embed with circuit breaker

    Trips after 5 failures, recovers after 60 seconds
    """
    return await embeddings.embed_query(text)
```

## Testing Integration

### Test with Real Components

```python
import pytest
from uuid import uuid4

@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_pipeline():
    """Test complete integration"""

    # Setup
    processor = PDFProcessor()
    chunker = TextChunker()
    embeddings = E5Embeddings()
    qdrant = QdrantStore()

    # Process
    pages = processor.extract_pages("test.pdf")
    chunks = chunker.chunk_pages(pages)
    vectors = await embeddings.embed_chunks(chunks)

    case_id = uuid4()
    doc_id = uuid4()
    count = qdrant.store_chunks(case_id, doc_id, chunks, vectors)

    assert count == len(chunks)

    # Search
    query_vec = await embeddings.embed_query("test query")
    results = qdrant.search_chunks(query_vec, case_id=case_id)

    assert len(results) > 0

    # Cleanup
    qdrant.delete_document_chunks(doc_id)
    await embeddings.close()
```

## Configuration Best Practices

### Environment Variables

```bash
# LM Studio
LLM_ENDPOINT=http://192.168.200.226:1234/v1
EMBEDDING_MODEL=intfloat/multilingual-e5-large
EMBEDDING_DIMENSION=1024
EMBEDDING_BATCH_SIZE=32

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=document_chunks
QDRANT_TIMEOUT=60

# Processing
CHUNK_SIZE=750
CHUNK_OVERLAP=120
MAX_WORKERS=4
```

### Settings Validation

```python
from pydantic import validator

class Settings(BaseSettings):
    embedding_dimension: int = 1024

    @validator("embedding_dimension")
    def validate_dimension(cls, v):
        if v != 1024:
            raise ValueError("E5-large requires 1024 dimensions")
        return v
```

## Deployment Checklist

- [ ] LM Studio running with E5-large model loaded
- [ ] Qdrant running and accessible
- [ ] Collection `document_chunks` created
- [ ] Environment variables configured
- [ ] Dependencies installed (`tenacity==8.2.3`)
- [ ] Health checks passing
- [ ] Integration tests passing
- [ ] Monitoring configured
- [ ] Logging configured
- [ ] Error alerts configured

## Troubleshooting

### Common Issues

1. **Import Error: No module named 'tenacity'**
   - Solution: `pip install tenacity==8.2.3`

2. **Dimension Mismatch (expected 1024, got 768)**
   - Solution: Verify E5-large model loaded in LM Studio (not E5-base)

3. **TimeoutException**
   - Solution: Increase `timeout` parameter or reduce `batch_size`

4. **Connection Refused**
   - Solution: Check LM Studio running at correct endpoint

5. **Low Retrieval Quality**
   - Solution: Verify E5 prefixes applied correctly (query vs passage)

## Next Steps

1. **Phase 2 Features**:
   - Query expansion
   - Hybrid search (vector + BM25)
   - Cross-encoder reranking

2. **Optimizations**:
   - Connection pooling
   - Embedding caching
   - Batch size tuning

3. **Evaluation**:
   - Build test dataset
   - Measure Precision@5 and MRR
   - A/B test different configurations
