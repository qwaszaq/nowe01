"""
Redis Caching Layer
Handles fast caching for micro-agents, embeddings, and session state
"""

import logging
import hashlib
import json
from typing import Dict, List, Any, Optional
import redis
from redis.connection import ConnectionPool

from src.config import settings

logger = logging.getLogger(__name__)


class RedisStore:
    """Redis cache manager with connection pooling"""

    # Cache key patterns
    KEY_MICRO_AGENT = "micro_agent:{agent_name}:{input_hash}"
    KEY_EMBEDDING = "embeddings:{text_hash}"
    KEY_ANALYSIS = "analysis:{case_id}"
    KEY_SESSION = "session:{session_id}"
    KEY_RATE_LIMIT = "rate_limit:{identifier}"

    # Default TTL values (seconds)
    TTL_MICRO_AGENT = 86400  # 24 hours
    TTL_EMBEDDING = 86400  # 24 hours
    TTL_ANALYSIS = 7200  # 2 hours
    TTL_SESSION = 3600  # 1 hour
    TTL_RATE_LIMIT = 60  # 1 minute

    def __init__(self):
        """Initialize Redis connection pool"""
        self.pool = None
        self.client = None
        self._initialize_pool()

    def _initialize_pool(self):
        """Initialize connection pool"""
        try:
            # Create connection pool
            self.pool = ConnectionPool(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password,
                max_connections=20,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )

            # Create client from pool
            self.client = redis.Redis(connection_pool=self.pool)

            # Test connection
            self.client.ping()
            logger.info(f"Redis connection pool initialized: {settings.redis_host}:{settings.redis_port}")

        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            logger.warning("Redis unavailable - cache will be disabled")
            self.client = None
            self.pool = None
        except Exception as e:
            logger.error(f"Failed to initialize Redis pool: {e}")
            self.client = None
            self.pool = None

    def _is_available(self) -> bool:
        """Check if Redis is available"""
        return self.client is not None

    def _make_key(self, key: str) -> str:
        """Add prefix to key"""
        return f"{settings.redis_key_prefix}{key}"

    def _hash_text(self, text: str) -> str:
        """Create hash of text for cache key"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    # =========================================================================
    # BASIC OPERATIONS
    # =========================================================================

    def get(self, key: str) -> Optional[str]:
        """
        Get cached value by key

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or error
        """
        if not self._is_available():
            return None

        try:
            full_key = self._make_key(key)
            value = self.client.get(full_key)
            if value:
                logger.debug(f"Cache HIT: {key}")
            return value

        except Exception as e:
            logger.error(f"Redis GET error for key '{key}': {e}")
            return None

    def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """
        Set cached value with optional TTL

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)

        Returns:
            True if successful, False otherwise
        """
        if not self._is_available():
            return False

        try:
            full_key = self._make_key(key)
            if ttl:
                self.client.setex(full_key, ttl, value)
            else:
                self.client.set(full_key, value)

            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True

        except Exception as e:
            logger.error(f"Redis SET error for key '{key}': {e}")
            return False

    def setex(self, key: str, ttl: int, value: str) -> bool:
        """
        Set cached value with expiry time

        Args:
            key: Cache key
            ttl: Time to live in seconds
            value: Value to cache

        Returns:
            True if successful, False otherwise
        """
        if not self._is_available():
            return False

        try:
            full_key = self._make_key(key)
            self.client.setex(full_key, ttl, value)
            logger.debug(f"Cache SETEX: {key} (TTL: {ttl}s)")
            return True

        except Exception as e:
            logger.error(f"Redis SETEX error for key '{key}': {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete cached value

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False otherwise
        """
        if not self._is_available():
            return False

        try:
            full_key = self._make_key(key)
            result = self.client.delete(full_key)
            if result > 0:
                logger.debug(f"Cache DELETE: {key}")
                return True
            return False

        except Exception as e:
            logger.error(f"Redis DELETE error for key '{key}': {e}")
            return False

    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        if not self._is_available():
            return False

        try:
            full_key = self._make_key(key)
            return self.client.exists(full_key) > 0

        except Exception as e:
            logger.error(f"Redis EXISTS error for key '{key}': {e}")
            return False

    # =========================================================================
    # HASH OPERATIONS
    # =========================================================================

    def hash_get(self, key: str, field: str) -> Optional[str]:
        """
        Get hash field value

        Args:
            key: Hash key
            field: Field name

        Returns:
            Field value or None
        """
        if not self._is_available():
            return None

        try:
            full_key = self._make_key(key)
            value = self.client.hget(full_key, field)
            if value:
                logger.debug(f"Cache HGET: {key}.{field}")
            return value

        except Exception as e:
            logger.error(f"Redis HGET error for key '{key}' field '{field}': {e}")
            return None

    def hash_set(self, key: str, field: str, value: str) -> bool:
        """
        Set hash field value

        Args:
            key: Hash key
            field: Field name
            value: Field value

        Returns:
            True if successful, False otherwise
        """
        if not self._is_available():
            return False

        try:
            full_key = self._make_key(key)
            self.client.hset(full_key, field, value)
            logger.debug(f"Cache HSET: {key}.{field}")
            return True

        except Exception as e:
            logger.error(f"Redis HSET error for key '{key}' field '{field}': {e}")
            return False

    def hash_get_all(self, key: str) -> Optional[Dict[str, str]]:
        """
        Get all hash fields

        Args:
            key: Hash key

        Returns:
            Dictionary of field:value pairs or None
        """
        if not self._is_available():
            return None

        try:
            full_key = self._make_key(key)
            result = self.client.hgetall(full_key)
            if result:
                logger.debug(f"Cache HGETALL: {key}")
            return result

        except Exception as e:
            logger.error(f"Redis HGETALL error for key '{key}': {e}")
            return None

    # =========================================================================
    # COUNTER OPERATIONS
    # =========================================================================

    def increment(self, key: str) -> int:
        """
        Increment counter

        Args:
            key: Counter key

        Returns:
            New counter value, or 0 on error
        """
        if not self._is_available():
            return 0

        try:
            full_key = self._make_key(key)
            value = self.client.incr(full_key)
            logger.debug(f"Cache INCR: {key} -> {value}")
            return value

        except Exception as e:
            logger.error(f"Redis INCR error for key '{key}': {e}")
            return 0

    def decrement(self, key: str) -> int:
        """
        Decrement counter

        Args:
            key: Counter key

        Returns:
            New counter value, or 0 on error
        """
        if not self._is_available():
            return 0

        try:
            full_key = self._make_key(key)
            value = self.client.decr(full_key)
            logger.debug(f"Cache DECR: {key} -> {value}")
            return value

        except Exception as e:
            logger.error(f"Redis DECR error for key '{key}': {e}")
            return 0

    # =========================================================================
    # HIGH-LEVEL CACHE METHODS
    # =========================================================================

    def cache_micro_agent_response(
        self,
        agent_name: str,
        input_text: str,
        response: str
    ) -> bool:
        """
        Cache micro-agent response

        Args:
            agent_name: Name of micro-agent
            input_text: Input text
            response: Agent response

        Returns:
            True if cached successfully
        """
        input_hash = self._hash_text(input_text)
        key = f"micro_agent:{agent_name}:{input_hash}"
        return self.setex(key, self.TTL_MICRO_AGENT, response)

    def get_micro_agent_response(
        self,
        agent_name: str,
        input_text: str
    ) -> Optional[str]:
        """
        Get cached micro-agent response

        Args:
            agent_name: Name of micro-agent
            input_text: Input text

        Returns:
            Cached response or None
        """
        input_hash = self._hash_text(input_text)
        key = f"micro_agent:{agent_name}:{input_hash}"
        return self.get(key)

    def cache_embedding(
        self,
        text: str,
        embedding: List[float]
    ) -> bool:
        """
        Cache text embedding

        Args:
            text: Original text
            embedding: Embedding vector

        Returns:
            True if cached successfully
        """
        text_hash = self._hash_text(text)
        key = f"embeddings:{text_hash}"
        value = json.dumps(embedding)
        return self.setex(key, self.TTL_EMBEDDING, value)

    def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Get cached embedding

        Args:
            text: Original text

        Returns:
            Embedding vector or None
        """
        text_hash = self._hash_text(text)
        key = f"embeddings:{text_hash}"
        value = self.get(key)

        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode embedding: {e}")
                return None

        return None

    def cache_analysis_result(
        self,
        case_id: str,
        analysis_data: Dict[str, Any]
    ) -> bool:
        """
        Cache analysis result

        Args:
            case_id: Case identifier
            analysis_data: Analysis result data

        Returns:
            True if cached successfully
        """
        key = f"analysis:{case_id}"
        value = json.dumps(analysis_data)
        return self.setex(key, self.TTL_ANALYSIS, value)

    def get_analysis_result(self, case_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached analysis result

        Args:
            case_id: Case identifier

        Returns:
            Analysis data or None
        """
        key = f"analysis:{case_id}"
        value = self.get(key)

        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode analysis result: {e}")
                return None

        return None

    def set_session_data(
        self,
        session_id: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        Store session data

        Args:
            session_id: Session identifier
            data: Session data

        Returns:
            True if stored successfully
        """
        key = f"session:{session_id}"
        value = json.dumps(data)
        return self.setex(key, self.TTL_SESSION, value)

    def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data

        Args:
            session_id: Session identifier

        Returns:
            Session data or None
        """
        key = f"session:{session_id}"
        value = self.get(key)

        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode session data: {e}")
                return None

        return None

    # =========================================================================
    # RATE LIMITING
    # =========================================================================

    def check_rate_limit(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int = 60
    ) -> bool:
        """
        Check if request is within rate limit

        Args:
            identifier: Client identifier (IP, user_id, etc)
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            True if allowed, False if rate limit exceeded
        """
        if not self._is_available():
            return True  # Allow if Redis unavailable

        try:
            key = f"rate_limit:{identifier}"
            full_key = self._make_key(key)

            # Increment counter
            current = self.client.incr(full_key)

            # Set expiry on first request
            if current == 1:
                self.client.expire(full_key, window_seconds)

            # Check if limit exceeded
            if current > max_requests:
                logger.warning(f"Rate limit exceeded for {identifier}: {current}/{max_requests}")
                return False

            return True

        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return True  # Allow on error

    # =========================================================================
    # HEALTH CHECK
    # =========================================================================

    def health_check(self) -> Dict[str, Any]:
        """
        Check Redis health and connectivity

        Returns:
            Health status dictionary
        """
        if not self._is_available():
            return {
                "status": "unavailable",
                "error": "Redis client not initialized"
            }

        try:
            # Test connection
            ping_result = self.client.ping()

            # Get info
            info = self.client.info()

            return {
                "status": "healthy",
                "ping": ping_result,
                "host": settings.redis_host,
                "port": settings.redis_port,
                "db": settings.redis_db,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace": info.get(f"db{settings.redis_db}", {})
            }

        except redis.ConnectionError as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": f"Connection error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    def close(self):
        """Close connection pool"""
        if self.pool:
            try:
                self.pool.disconnect()
                logger.info("Redis connection pool closed")
            except Exception as e:
                logger.error(f"Error closing Redis pool: {e}")

            self.client = None
            self.pool = None
