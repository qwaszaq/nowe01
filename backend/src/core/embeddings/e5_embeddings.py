"""
E5-Large Embeddings via LM Studio
Multilingual semantic embeddings for document retrieval
"""

import httpx
import logging
import time
from typing import List, Dict, Any, Optional
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

logger = logging.getLogger(__name__)


class E5Embeddings:
    """
    E5-large embeddings client for LM Studio

    Model: intfloat/multilingual-e5-large
    Dimensions: 1024
    Distance: Cosine similarity

    E5 Requirements:
    - Queries must have 'query: ' prefix
    - Documents must have 'passage: ' prefix
    - Max 512 tokens per text (auto-truncated by model)
    """

    def __init__(
        self,
        endpoint: str = "http://192.168.200.226:1234/v1",
        model: str = "intfloat/multilingual-e5-large",
        dimensions: int = 1024,
        timeout: int = 60,
        max_retries: int = 3
    ):
        """
        Initialize E5 embeddings client

        Args:
            endpoint: LM Studio API endpoint
            model: Model identifier
            dimensions: Expected embedding dimensions
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
        """
        self.endpoint = endpoint
        self.model = model
        self.dimensions = dimensions
        self.timeout = timeout
        self.max_retries = max_retries

        # Initialize HTTP client with timeout
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )

        logger.info(
            f"Initialized E5Embeddings: endpoint={endpoint}, "
            f"model={model}, dimensions={dimensions}"
        )

    def _preprocess_text(self, text: str, prefix: str = "passage") -> str:
        """
        Preprocess text for E5 model

        E5 requires specific prefixes for optimal performance:
        - 'query: ' for search queries
        - 'passage: ' for document chunks

        Args:
            text: Input text
            prefix: Prefix type ('query' or 'passage')

        Returns:
            Preprocessed text with prefix
        """
        # Validate prefix
        if prefix not in ["query", "passage"]:
            logger.warning(f"Invalid prefix '{prefix}', defaulting to 'passage'")
            prefix = "passage"

        # Clean text
        text = text.strip()

        # Add E5 prefix
        return f"{prefix}: {text}"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        reraise=True
    )
    async def embed_query(self, query: str) -> List[float]:
        """
        Embed a search query

        Args:
            query: Search query text

        Returns:
            Query embedding vector (1024-dim)

        Raises:
            httpx.HTTPStatusError: If API request fails
            ValueError: If embedding dimensions mismatch
        """
        # Preprocess with query prefix
        preprocessed = self._preprocess_text(query, prefix="query")

        # Embed single text
        embedding = await self._embed_single(preprocessed)

        logger.debug(f"Embedded query: '{query[:50]}...' -> {len(embedding)}D vector")
        return embedding

    async def embed_chunks(
        self,
        chunks: List[Dict[str, Any]],
        batch_size: int = 32
    ) -> List[List[float]]:
        """
        Embed document chunks in batches with progress logging

        Args:
            chunks: List of chunk dicts with 'text' field
            batch_size: Batch size for API calls (default: 32)

        Returns:
            List of embedding vectors (1024-dim each)

        Raises:
            httpx.HTTPStatusError: If API request fails
            ValueError: If chunks missing 'text' field or dimension mismatch
        """
        if not chunks:
            logger.warning("No chunks provided for embedding")
            return []

        # Validate chunks have 'text' field
        for idx, chunk in enumerate(chunks):
            if 'text' not in chunk:
                raise ValueError(f"Chunk at index {idx} missing 'text' field")

        all_embeddings = []
        total_batches = (len(chunks) + batch_size - 1) // batch_size
        start_time = time.time()

        logger.info(
            f"Starting batch embedding: {len(chunks)} chunks, "
            f"{total_batches} batches (batch_size={batch_size})"
        )

        for batch_idx in range(0, len(chunks), batch_size):
            batch = chunks[batch_idx:batch_idx + batch_size]
            batch_num = batch_idx // batch_size + 1

            # Preprocess texts with passage prefix
            texts = [
                self._preprocess_text(chunk['text'], prefix="passage")
                for chunk in batch
            ]

            try:
                # Embed batch
                batch_start = time.time()
                embeddings = await self._embed_batch(texts)
                batch_duration = time.time() - batch_start

                all_embeddings.extend(embeddings)

                # Progress logging
                chunks_per_sec = len(batch) / batch_duration if batch_duration > 0 else 0
                logger.info(
                    f"Batch {batch_num}/{total_batches}: "
                    f"Embedded {len(batch)} chunks in {batch_duration:.2f}s "
                    f"({chunks_per_sec:.1f} chunks/sec)"
                )

            except Exception as e:
                logger.error(
                    f"Failed to embed batch {batch_num}/{total_batches}: {e}",
                    exc_info=True
                )
                raise

        total_duration = time.time() - start_time
        avg_speed = len(chunks) / total_duration if total_duration > 0 else 0

        logger.info(
            f"Completed batch embedding: {len(chunks)} chunks in {total_duration:.2f}s "
            f"(avg: {avg_speed:.1f} chunks/sec)"
        )

        return all_embeddings

    async def _embed_single(self, text: str) -> List[float]:
        """
        Embed a single preprocessed text

        Args:
            text: Preprocessed text (with prefix)

        Returns:
            Embedding vector (1024-dim)

        Raises:
            httpx.HTTPStatusError: If API request fails
            ValueError: If embedding dimensions mismatch
        """
        embeddings = await self._embed_batch([text])
        return embeddings[0]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        reraise=True
    )
    async def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Call LM Studio embeddings API for batch of texts

        Args:
            texts: List of preprocessed texts

        Returns:
            List of embedding vectors

        Raises:
            httpx.HTTPStatusError: If API request fails
            ValueError: If embedding dimensions mismatch
        """
        try:
            # Call embeddings API
            response = await self.client.post(
                f"{self.endpoint}/embeddings",
                json={
                    "model": self.model,
                    "input": texts
                }
            )
            response.raise_for_status()

            # Parse response
            data = response.json()

            # Extract embeddings (sorted by index to maintain order)
            items = sorted(data["data"], key=lambda x: x["index"])
            embeddings = [item["embedding"] for item in items]

            # Validate dimensions
            for idx, emb in enumerate(embeddings):
                if len(emb) != self.dimensions:
                    raise ValueError(
                        f"Embedding dimension mismatch at index {idx}: "
                        f"expected {self.dimensions}D, got {len(emb)}D"
                    )

            return embeddings

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error calling embeddings API: {e.response.status_code} - "
                f"{e.response.text}"
            )
            raise
        except httpx.TimeoutException as e:
            logger.error(f"Timeout calling embeddings API: {e}")
            raise
        except httpx.NetworkError as e:
            logger.error(f"Network error calling embeddings API: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling embeddings API: {e}", exc_info=True)
            raise

    async def health_check(self) -> Dict[str, Any]:
        """
        Check if LM Studio embeddings endpoint is healthy

        Returns:
            Health status dict with endpoint info
        """
        try:
            # Test with simple query
            test_text = self._preprocess_text("test", prefix="query")
            embedding = await self._embed_single(test_text)

            return {
                "status": "healthy",
                "endpoint": self.endpoint,
                "model": self.model,
                "dimensions": len(embedding),
                "expected_dimensions": self.dimensions
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "endpoint": self.endpoint,
                "error": str(e)
            }

    async def close(self):
        """Close HTTP client connection"""
        await self.client.aclose()
        logger.info("E5Embeddings client closed")

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
