"""
Semantic Search Orchestration Layer
Integrates E5 embeddings with Qdrant vector store for intelligent document retrieval
"""

import logging
from typing import List, Dict, Any, Optional
from uuid import UUID

# Note: E5Embeddings will be created by parallel agent
# from src.core.embeddings.e5_embeddings import E5Embeddings
from src.storage.qdrant_store import QdrantStore

logger = logging.getLogger(__name__)


class SemanticSearch:
    """
    Semantic search orchestration layer

    Coordinates query embedding generation and vector search to retrieve
    relevant document chunks with metadata and optional context windows.

    Features:
    - Basic semantic search with filtering
    - Context window retrieval (±N chunks around matches)
    - Score thresholding for quality control
    - Case/document/page filtering

    Quality Targets:
    - Precision@5: > 80%
    - Mean Reciprocal Rank: > 0.7
    - Average cosine similarity: > 0.75
    """

    def __init__(self, embeddings_service, qdrant_store: QdrantStore):
        """
        Initialize semantic search

        Args:
            embeddings_service: E5Embeddings instance (will be E5Embeddings class)
            qdrant_store: QdrantStore instance for vector operations
        """
        self.embeddings = embeddings_service
        self.qdrant = qdrant_store
        logger.info("SemanticSearch initialized")

    async def search(
        self,
        query: str,
        case_id: Optional[UUID] = None,
        document_id: Optional[UUID] = None,
        limit: int = 10,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for relevant document chunks

        Workflow:
        1. Embed query with E5 'query:' prefix
        2. Search Qdrant with cosine similarity
        3. Apply optional filters (case_id, document_id)
        4. Return top-k chunks with scores above threshold

        Args:
            query: Natural language search query
            case_id: Optional case UUID filter
            document_id: Optional document UUID filter
            limit: Maximum number of results to return
            score_threshold: Minimum cosine similarity score (0-1)

        Returns:
            List of matching chunks with structure:
            [
                {
                    'chunk_id': str,
                    'document_id': UUID,
                    'case_id': UUID,
                    'page_num': int,
                    'text': str,
                    'score': float,
                    'char_count': int
                },
                ...
            ]

        Example:
            >>> results = await search.search(
            ...     query="What is the company's debt level?",
            ...     case_id=UUID("123..."),
            ...     limit=5,
            ...     score_threshold=0.75
            ... )
        """
        try:
            # Step 1: Embed query with 'query:' prefix (E5 requirement)
            logger.info(f"Embedding query: {query[:100]}...")
            query_vector = await self.embeddings.embed_query(query)

            # Validate embedding dimensions
            if len(query_vector) != 1024:
                raise ValueError(f"Expected 1024-dim vector, got {len(query_vector)}")

            # Step 2: Search Qdrant vector store
            logger.info(
                f"Searching Qdrant (case={case_id}, doc={document_id}, "
                f"limit={limit}, threshold={score_threshold})"
            )
            results = self.qdrant.search_chunks(
                query_embedding=query_vector,
                case_id=case_id,
                document_id=document_id,
                limit=limit,
                score_threshold=score_threshold
            )

            # Log quality metrics
            if results:
                avg_score = sum(r['score'] for r in results) / len(results)
                logger.info(
                    f"Retrieved {len(results)} chunks. "
                    f"Avg score: {avg_score:.3f}, Top score: {results[0]['score']:.3f}"
                )
            else:
                logger.warning(f"No results found for query: {query[:100]}")

            return results

        except Exception as e:
            logger.error(f"Search failed: {e}", exc_info=True)
            raise

    async def search_with_context(
        self,
        query: str,
        window_size: int = 1,
        case_id: Optional[UUID] = None,
        document_id: Optional[UUID] = None,
        limit: int = 10,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search and return chunks with surrounding context

        For each matching chunk, retrieves ±N surrounding chunks from the
        same document page to provide better context for understanding.

        Workflow:
        1. Perform semantic search
        2. For each match, fetch surrounding chunks
        3. Return enriched results with context window

        Args:
            query: Natural language search query
            window_size: Number of chunks before/after to include
            case_id: Optional case UUID filter
            document_id: Optional document UUID filter
            limit: Maximum number of results to return
            score_threshold: Minimum cosine similarity score

        Returns:
            List of matches with context:
            [
                {
                    'chunk_id': str,
                    'document_id': UUID,
                    'case_id': UUID,
                    'page_num': int,
                    'chunk_idx': int,
                    'text': str,
                    'score': float,
                    'char_count': int,
                    'context': {
                        'before': [chunk_dict, ...],  # Previous chunks
                        'after': [chunk_dict, ...]     # Following chunks
                    }
                },
                ...
            ]

        Example:
            >>> results = await search.search_with_context(
            ...     query="Revenue analysis",
            ...     window_size=2,  # Include 2 chunks before and after
            ...     limit=5
            ... )
        """
        try:
            # Get initial matches
            matches = await self.search(
                query=query,
                case_id=case_id,
                document_id=document_id,
                limit=limit,
                score_threshold=score_threshold
            )

            if not matches:
                return []

            # Enrich each match with context window
            enriched_results = []
            for match in matches:
                try:
                    context = await self._get_context_window(
                        document_id=match['document_id'],
                        page_num=match['page_num'],
                        chunk_idx=match.get('chunk_idx', 0),
                        window_size=window_size
                    )

                    enriched_results.append({
                        **match,
                        'context': context
                    })

                except Exception as e:
                    logger.warning(
                        f"Failed to get context for chunk {match['chunk_id']}: {e}"
                    )
                    # Include match without context
                    enriched_results.append({
                        **match,
                        'context': {'before': [], 'after': []}
                    })

            logger.info(
                f"Enriched {len(enriched_results)} results with context "
                f"(window_size={window_size})"
            )

            return enriched_results

        except Exception as e:
            logger.error(f"Context search failed: {e}", exc_info=True)
            raise

    async def _get_context_window(
        self,
        document_id: UUID,
        page_num: int,
        chunk_idx: int,
        window_size: int
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieve surrounding chunks for context

        Fetches chunks from the same document/page that appear before
        and after the target chunk index.

        Args:
            document_id: Document UUID
            page_num: Page number
            chunk_idx: Target chunk index
            window_size: Number of chunks before/after

        Returns:
            Dictionary with 'before' and 'after' chunk lists:
            {
                'before': [chunk_dict, ...],  # Ordered oldest to newest
                'after': [chunk_dict, ...]     # Ordered newest to oldest
            }
        """
        try:
            # Get all chunks for document
            all_chunks = self.qdrant.get_chunks_by_document(
                document_id=document_id,
                limit=1000
            )

            # Filter to same page
            page_chunks = [
                c for c in all_chunks
                if c['page_num'] == page_num
            ]

            # Sort by chunk index
            page_chunks.sort(key=lambda x: x['chunk_idx'])

            # Find target chunk position
            target_pos = None
            for i, chunk in enumerate(page_chunks):
                if chunk['chunk_idx'] == chunk_idx:
                    target_pos = i
                    break

            if target_pos is None:
                logger.warning(
                    f"Target chunk not found: doc={document_id}, "
                    f"page={page_num}, idx={chunk_idx}"
                )
                return {'before': [], 'after': []}

            # Extract context windows
            before_start = max(0, target_pos - window_size)
            before_chunks = page_chunks[before_start:target_pos]

            after_end = min(len(page_chunks), target_pos + window_size + 1)
            after_chunks = page_chunks[target_pos + 1:after_end]

            logger.debug(
                f"Context window: {len(before_chunks)} before, "
                f"{len(after_chunks)} after"
            )

            return {
                'before': before_chunks,
                'after': after_chunks
            }

        except Exception as e:
            logger.error(f"Failed to get context window: {e}", exc_info=True)
            return {'before': [], 'after': []}

    async def multi_query_search(
        self,
        queries: List[str],
        case_id: Optional[UUID] = None,
        document_id: Optional[UUID] = None,
        limit: int = 10,
        score_threshold: float = 0.7,
        merge_strategy: str = "max"
    ) -> List[Dict[str, Any]]:
        """
        Search with multiple queries and merge results

        Useful for query expansion and improving recall by searching
        with multiple related queries and combining results.

        Args:
            queries: List of search queries
            case_id: Optional case UUID filter
            document_id: Optional document UUID filter
            limit: Maximum number of results to return
            score_threshold: Minimum cosine similarity score
            merge_strategy: How to merge scores ("max", "avg", "sum")

        Returns:
            Merged list of unique chunks with combined scores

        Example:
            >>> results = await search.multi_query_search(
            ...     queries=[
            ...         "What is the company's debt?",
            ...         "Debt to equity ratio analysis",
            ...         "Leverage and borrowing levels"
            ...     ],
            ...     merge_strategy="max"
            ... )
        """
        try:
            # Search with each query
            all_results = []
            for query in queries:
                results = await self.search(
                    query=query,
                    case_id=case_id,
                    document_id=document_id,
                    limit=limit,
                    score_threshold=score_threshold
                )
                all_results.append(results)

            # Merge results by chunk_id
            merged = {}
            for results in all_results:
                for chunk in results:
                    chunk_id = chunk['chunk_id']

                    if chunk_id not in merged:
                        merged[chunk_id] = chunk
                        merged[chunk_id]['scores'] = [chunk['score']]
                    else:
                        merged[chunk_id]['scores'].append(chunk['score'])

            # Apply merge strategy
            for chunk_id, chunk in merged.items():
                scores = chunk['scores']

                if merge_strategy == "max":
                    chunk['score'] = max(scores)
                elif merge_strategy == "avg":
                    chunk['score'] = sum(scores) / len(scores)
                elif merge_strategy == "sum":
                    chunk['score'] = sum(scores)
                else:
                    raise ValueError(f"Unknown merge strategy: {merge_strategy}")

                # Remove temporary scores list
                del chunk['scores']

            # Sort by merged score and limit
            final_results = sorted(
                merged.values(),
                key=lambda x: x['score'],
                reverse=True
            )[:limit]

            logger.info(
                f"Multi-query search: {len(queries)} queries, "
                f"{len(merged)} unique chunks, returned {len(final_results)}"
            )

            return final_results

        except Exception as e:
            logger.error(f"Multi-query search failed: {e}", exc_info=True)
            raise

    async def filtered_search(
        self,
        query: str,
        page_num: Optional[int] = None,
        min_char_count: Optional[int] = None,
        max_char_count: Optional[int] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Search with additional post-filtering

        Performs semantic search and applies additional filters
        on chunk metadata.

        Args:
            query: Search query
            page_num: Filter to specific page number
            min_char_count: Minimum chunk character count
            max_char_count: Maximum chunk character count
            **kwargs: Additional search parameters

        Returns:
            Filtered list of matching chunks
        """
        try:
            # Perform base search
            results = await self.search(query=query, **kwargs)

            # Apply post-filters
            filtered = results

            if page_num is not None:
                filtered = [r for r in filtered if r['page_num'] == page_num]

            if min_char_count is not None:
                filtered = [r for r in filtered if r['char_count'] >= min_char_count]

            if max_char_count is not None:
                filtered = [r for r in filtered if r['char_count'] <= max_char_count]

            logger.info(
                f"Filtered search: {len(results)} -> {len(filtered)} results"
            )

            return filtered

        except Exception as e:
            logger.error(f"Filtered search failed: {e}", exc_info=True)
            raise

    def get_quality_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate quality metrics for search results

        Args:
            results: List of search results with scores

        Returns:
            Dictionary with quality metrics:
            {
                'result_count': int,
                'avg_score': float,
                'min_score': float,
                'max_score': float,
                'score_std': float,
                'above_75': int,  # Count with score > 0.75
                'above_80': int,  # Count with score > 0.80
                'meets_target': bool  # avg_score > 0.75
            }
        """
        if not results:
            return {
                'result_count': 0,
                'avg_score': 0.0,
                'min_score': 0.0,
                'max_score': 0.0,
                'score_std': 0.0,
                'above_75': 0,
                'above_80': 0,
                'meets_target': False
            }

        scores = [r['score'] for r in results]
        avg_score = sum(scores) / len(scores)

        # Calculate standard deviation
        variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
        std = variance ** 0.5

        return {
            'result_count': len(results),
            'avg_score': avg_score,
            'min_score': min(scores),
            'max_score': max(scores),
            'score_std': std,
            'above_75': sum(1 for s in scores if s > 0.75),
            'above_80': sum(1 for s in scores if s > 0.80),
            'meets_target': avg_score > 0.75
        }
