"""
LM Studio Client for Local LLM Integration
Provides HTTP client for LM Studio API with retry logic and error handling
"""

import httpx
import asyncio
import logging
from typing import Dict, List, Optional, Any
from functools import wraps

from src.config.settings import settings

logger = logging.getLogger(__name__)


class LMStudioError(Exception):
    """Base exception for LM Studio client errors"""
    pass


class LMStudioConnectionError(LMStudioError):
    """Raised when unable to connect to LM Studio server"""
    pass


class LMStudioTimeoutError(LMStudioError):
    """Raised when request times out"""
    pass


class LMStudioClient:
    """
    HTTP client for LM Studio local LLM server

    Supports:
    - Chat completions (micro-agents)
    - Text embeddings
    - Automatic retry with exponential backoff
    - Connection pooling
    - Timeout handling
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None
    ):
        """
        Initialize LM Studio client

        Args:
            endpoint: LM Studio API endpoint (default from settings)
            timeout: Request timeout in seconds (default from settings)
            max_retries: Maximum retry attempts (default from settings)
        """
        self.endpoint = endpoint or settings.llm_endpoint
        self.timeout = timeout or settings.llm_timeout
        self.max_retries = max_retries or settings.llm_max_retries

        # Create HTTP client with connection pooling
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20)
        )

        logger.info(f"LM Studio client initialized: {self.endpoint}")

    async def chat_completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Execute chat completion for micro-agent classification

        Optimized for:
        - Short prompts (< 50 tokens)
        - Single-token responses
        - Deterministic output (low temperature)

        Args:
            prompt: User prompt (keep under 50 tokens for micro-agents)
            model: Model name (oss or gemma, defaults to gemma)
            max_tokens: Maximum output tokens (default 10)
            temperature: Temperature for sampling (default 0.1 for deterministic)
            system_prompt: Optional system prompt for context

        Returns:
            Model response text (stripped)

        Raises:
            LMStudioConnectionError: If connection fails
            LMStudioTimeoutError: If request times out
        """
        model = model or settings.llm_default_model
        max_tokens = max_tokens or settings.llm_max_tokens
        temperature = temperature or settings.llm_temperature

        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Retry loop with exponential backoff
        for attempt in range(self.max_retries):
            try:
                response = await self.client.post(
                    f"{self.endpoint}/chat/completions",
                    json={
                        "model": model,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "stream": False
                    }
                )

                response.raise_for_status()
                data = response.json()

                # Extract response text
                result = data["choices"][0]["message"]["content"].strip()

                logger.debug(
                    f"LLM call successful (attempt {attempt + 1}/{self.max_retries}): "
                    f"{len(prompt)} chars -> {len(result)} chars"
                )

                return result

            except httpx.TimeoutException as e:
                logger.warning(f"LM Studio timeout (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                raise LMStudioTimeoutError(f"Request timed out after {self.max_retries} attempts") from e

            except httpx.ConnectError as e:
                logger.warning(f"LM Studio connection error (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise LMStudioConnectionError(f"Unable to connect to LM Studio at {self.endpoint}") from e

            except httpx.HTTPStatusError as e:
                logger.error(f"LM Studio HTTP error: {e.response.status_code} - {e.response.text}")
                raise LMStudioError(f"HTTP {e.response.status_code}: {e.response.text}") from e

            except Exception as e:
                logger.error(f"Unexpected error in LM Studio call: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise LMStudioError(f"Unexpected error: {e}") from e

    async def embeddings(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """
        Generate embeddings for text using LM Studio

        Args:
            texts: List of texts to embed
            model: Embedding model name (default from settings)

        Returns:
            List of embedding vectors (each is List[float])

        Raises:
            LMStudioConnectionError: If connection fails
            LMStudioTimeoutError: If request times out
        """
        model = model or settings.embedding_model

        # LM Studio embeddings endpoint
        for attempt in range(self.max_retries):
            try:
                response = await self.client.post(
                    f"{self.endpoint}/embeddings",
                    json={
                        "model": model,
                        "input": texts
                    }
                )

                response.raise_for_status()
                data = response.json()

                # Extract embeddings
                embeddings = [item["embedding"] for item in data["data"]]

                logger.debug(f"Generated {len(embeddings)} embeddings")

                return embeddings

            except httpx.TimeoutException as e:
                logger.warning(f"Embeddings timeout (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise LMStudioTimeoutError(f"Embeddings request timed out") from e

            except httpx.ConnectError as e:
                logger.warning(f"Embeddings connection error (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise LMStudioConnectionError(f"Unable to connect for embeddings") from e

            except Exception as e:
                logger.error(f"Error generating embeddings: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise LMStudioError(f"Embeddings error: {e}") from e

    async def health_check(self) -> Dict[str, Any]:
        """
        Check LM Studio server health

        Returns:
            Health status dictionary with connection info
        """
        try:
            response = await self.client.get(f"{self.endpoint}/models", timeout=5.0)
            response.raise_for_status()

            models = response.json()

            return {
                "status": "healthy",
                "endpoint": self.endpoint,
                "models": models.get("data", []),
                "accessible": True
            }

        except Exception as e:
            logger.error(f"LM Studio health check failed: {e}")
            return {
                "status": "unhealthy",
                "endpoint": self.endpoint,
                "error": str(e),
                "accessible": False
            }

    async def close(self):
        """Close HTTP client connection pool"""
        await self.client.aclose()
        logger.info("LM Studio client connections closed")

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


# Global client instance (initialized on demand)
_global_client: Optional[LMStudioClient] = None


def get_lm_studio_client() -> LMStudioClient:
    """
    Get or create global LM Studio client instance

    Returns:
        Shared LMStudioClient instance
    """
    global _global_client

    if _global_client is None:
        _global_client = LMStudioClient()

    return _global_client
