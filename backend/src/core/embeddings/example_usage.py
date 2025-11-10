"""
Example Usage: E5 Embeddings Pipeline Integration
Demonstrates end-to-end workflow: chunks -> embeddings -> Qdrant storage
"""

import asyncio
import logging
from uuid import uuid4
from typing import List, Dict, Any

from src.config import settings
from src.core.embeddings import E5Embeddings
from src.storage.qdrant_store import QdrantStore
from src.core.extractors.text_chunker import TextChunker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_embed_and_store():
    """
    Example: Embed document chunks and store in Qdrant
    """
    # Initialize components
    embeddings = E5Embeddings(
        endpoint=settings.llm_endpoint,
        model=settings.embedding_model,
        dimensions=settings.embedding_dimension
    )
    qdrant = QdrantStore()
    chunker = TextChunker(
        chunk_size=settings.chunk_size,
        overlap=settings.chunk_overlap
    )

    # Sample document pages (normally from PDFProcessor)
    sample_pages = [
        {
            "page_num": 1,
            "text": "Company XYZ reported revenue of $10 million in Q4 2023. "
                    "This represents a 15% increase year-over-year. The company's "
                    "debt-to-equity ratio stands at 0.45, indicating moderate leverage."
        },
        {
            "page_num": 2,
            "text": "Net profit margin improved to 8.2% from 6.5% in the previous year. "
                    "Operating expenses were reduced by 12% through efficiency initiatives. "
                    "Cash flow from operations reached $2.3 million."
        }
    ]

    # Step 1: Chunk the pages
    logger.info("Step 1: Chunking pages...")
    chunks = chunker.chunk_pages(sample_pages)
    logger.info(f"Created {len(chunks)} chunks")

    # Step 2: Generate embeddings
    logger.info("Step 2: Generating embeddings...")
    embeddings_vectors = await embeddings.embed_chunks(chunks, batch_size=32)
    logger.info(f"Generated {len(embeddings_vectors)} embeddings")

    # Step 3: Store in Qdrant
    logger.info("Step 3: Storing in Qdrant...")
    case_id = uuid4()
    document_id = uuid4()

    stored_count = qdrant.store_chunks(
        case_id=case_id,
        document_id=document_id,
        chunks=chunks,
        embeddings=embeddings_vectors
    )
    logger.info(f"Stored {stored_count} chunks in Qdrant")

    # Step 4: Test semantic search
    logger.info("Step 4: Testing semantic search...")
    query = "What is the company's profitability?"
    query_embedding = await embeddings.embed_query(query)

    results = qdrant.search_chunks(
        query_embedding=query_embedding,
        case_id=case_id,
        limit=3,
        score_threshold=0.5
    )

    logger.info(f"Found {len(results)} matching chunks:")
    for idx, result in enumerate(results, 1):
        logger.info(
            f"  {idx}. Score: {result['score']:.3f} | "
            f"Page: {result['page_num']} | "
            f"Text: {result['text'][:100]}..."
        )

    # Cleanup
    await embeddings.close()
    logger.info("Example completed successfully!")


async def example_health_check():
    """
    Example: Check embeddings service health
    """
    embeddings = E5Embeddings(
        endpoint=settings.llm_endpoint,
        model=settings.embedding_model,
        dimensions=settings.embedding_dimension
    )

    health = await embeddings.health_check()
    logger.info(f"Health check result: {health}")

    await embeddings.close()


async def example_batch_processing():
    """
    Example: Process large batch of chunks with progress tracking
    """
    embeddings = E5Embeddings(
        endpoint=settings.llm_endpoint,
        model=settings.embedding_model,
        dimensions=settings.embedding_dimension
    )

    # Create 100 sample chunks
    sample_chunks = [
        {
            "chunk_id": f"chunk_{i}",
            "text": f"This is sample chunk number {i} with some financial data. "
                    f"Revenue: ${i * 1000}, Profit margin: {i / 10}%",
            "page_num": i // 10 + 1,
            "chunk_idx": i % 10,
            "char_count": 100,
            "word_count": 20
        }
        for i in range(100)
    ]

    logger.info(f"Processing {len(sample_chunks)} chunks...")
    embeddings_vectors = await embeddings.embed_chunks(
        sample_chunks,
        batch_size=32
    )
    logger.info(f"Generated {len(embeddings_vectors)} embeddings")

    # Verify dimensions
    for idx, vec in enumerate(embeddings_vectors[:3]):
        logger.info(f"Chunk {idx}: {len(vec)}-dimensional vector")

    await embeddings.close()


async def example_query_vs_passage():
    """
    Example: Demonstrate query vs passage prefix difference
    """
    embeddings = E5Embeddings(
        endpoint=settings.llm_endpoint,
        model=settings.embedding_model,
        dimensions=settings.embedding_dimension
    )

    query_text = "financial performance metrics"

    # Embed as query (correct for search)
    query_embedding = await embeddings.embed_query(query_text)
    logger.info(f"Query embedding: {len(query_embedding)}D vector")

    # Embed as passage (for comparison - not recommended for queries)
    passage_embedding = await embeddings.embed_chunks(
        [{"text": query_text}],
        batch_size=1
    )
    logger.info(f"Passage embedding: {len(passage_embedding[0])}D vector")

    # Note: These will be different due to E5's prefix sensitivity
    logger.info(
        "Note: Query and passage embeddings differ due to E5 prefix requirements. "
        "Always use embed_query() for search queries and embed_chunks() for documents."
    )

    await embeddings.close()


if __name__ == "__main__":
    # Run examples
    print("\n" + "=" * 60)
    print("E5 Embeddings Pipeline Examples")
    print("=" * 60 + "\n")

    # Example 1: Full pipeline
    print("\n--- Example 1: Full Pipeline (Chunk -> Embed -> Store -> Search) ---")
    asyncio.run(example_embed_and_store())

    # Example 2: Health check
    print("\n--- Example 2: Health Check ---")
    asyncio.run(example_health_check())

    # Example 3: Batch processing
    print("\n--- Example 3: Batch Processing ---")
    asyncio.run(example_batch_processing())

    # Example 4: Query vs Passage
    print("\n--- Example 4: Query vs Passage Prefixes ---")
    asyncio.run(example_query_vs_passage())

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)
