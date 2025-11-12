"""
Qdrant Vector Store
Handles embeddings and semantic search
"""

import logging
from typing import Dict, List, Any, Optional
from uuid import UUID
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct

from src.config import settings

logger = logging.getLogger(__name__)


class QdrantStore:
    """Qdrant vector database manager for embeddings"""

    COLLECTION_CHUNKS = "document_chunks"
    VECTOR_SIZE = 1024  # multilingual-e5-large dimension

    def __init__(self):
        self.client = None
        self._connect()
        self._initialize_collections()

    def _connect(self):
        """Connect to Qdrant"""
        try:
            self.client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
                timeout=settings.qdrant_timeout
            )
            logger.info(f"Connected to Qdrant at {settings.qdrant_host}:{settings.qdrant_port}")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise

    def _initialize_collections(self):
        """Create collections if they don't exist"""
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.COLLECTION_CHUNKS not in collection_names:
                self.client.create_collection(
                    collection_name=self.COLLECTION_CHUNKS,
                    vectors_config=VectorParams(
                        size=self.VECTOR_SIZE,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {self.COLLECTION_CHUNKS}")

                # Create payload indexes for filtering
                self.client.create_payload_index(
                    collection_name=self.COLLECTION_CHUNKS,
                    field_name="case_id",
                    field_schema=models.PayloadSchemaType.KEYWORD
                )
                self.client.create_payload_index(
                    collection_name=self.COLLECTION_CHUNKS,
                    field_name="document_id",
                    field_schema=models.PayloadSchemaType.KEYWORD
                )
                self.client.create_payload_index(
                    collection_name=self.COLLECTION_CHUNKS,
                    field_name="page_num",
                    field_schema=models.PayloadSchemaType.INTEGER
                )
                logger.info("Created payload indexes")
            else:
                logger.info(f"Collection {self.COLLECTION_CHUNKS} already exists")

        except Exception as e:
            logger.error(f"Failed to initialize collections: {e}")
            raise

    # =========================================================================
    # CHUNK OPERATIONS
    # =========================================================================

    def store_chunks(
        self,
        case_id: UUID,
        document_id: UUID,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]]
    ) -> int:
        """
        Store document chunks with embeddings

        Args:
            case_id: Case UUID
            document_id: Document UUID
            chunks: List of chunk dicts from TextChunker
            embeddings: List of embedding vectors (1024-dim)

        Returns:
            Number of chunks stored
        """
        if len(chunks) != len(embeddings):
            raise ValueError(f"Chunks count ({len(chunks)}) != embeddings count ({len(embeddings)})")

        if not chunks:
            return 0

        # Prepare points for Qdrant
        points = []
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            # Base payload fields (always present)
            payload = {
                'chunk_id': chunk['chunk_id'],
                'case_id': str(case_id),
                'document_id': str(document_id),
                'page_num': chunk['page_num'],
                'chunk_idx': chunk['chunk_idx'],
                'text': chunk['text'],
                'char_count': chunk['char_count'],
                'word_count': chunk['word_count'],
                'is_complete_page': chunk.get('is_complete_page', False)
            }

            # NEW: Enhanced metadata fields (from StructureAwareChunker)
            # These fields enable filtering and display of structure-aware chunks
            chunk_metadata = chunk.get('metadata', {})
            if chunk_metadata:
                # Chunk type: text, table, or mixed
                if 'type' in chunk_metadata:
                    payload['chunk_type'] = chunk_metadata['type']

                # Temporal context: List of years (e.g., ["2024", "2023"])
                if 'temporal_context' in chunk_metadata:
                    temporal_context = chunk_metadata['temporal_context']
                    if temporal_context:
                        payload['temporal_context'] = temporal_context
                        # Also store as comma-separated string for easy text search
                        payload['temporal_context_str'] = ','.join(temporal_context)

                # Table headers preservation flag
                if 'has_complete_headers' in chunk_metadata:
                    payload['has_complete_headers'] = chunk_metadata['has_complete_headers']

                # Table section indicator (e.g., "1/3" means chunk 1 of 3 from this table)
                if 'table_section' in chunk_metadata:
                    payload['table_section'] = chunk_metadata['table_section']

                # Table ID for grouping chunks from same table
                if 'table_id' in chunk_metadata:
                    payload['table_id'] = chunk_metadata['table_id']

            point = PointStruct(
                id=hash(chunk['chunk_id']) & 0x7FFFFFFFFFFFFFFF,  # Convert to positive int
                vector=embedding,
                payload=payload
            )
            points.append(point)

        # Batch upsert in smaller batches to avoid timeout
        try:
            batch_size = 500
            total_stored = 0

            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                self.client.upsert(
                    collection_name=self.COLLECTION_CHUNKS,
                    points=batch
                )
                total_stored += len(batch)
                if len(points) > batch_size:
                    logger.info(f"Stored batch {i//batch_size + 1}/{(len(points)-1)//batch_size + 1}: {len(batch)} chunks")

            logger.info(f"Stored {total_stored} chunks for document {document_id}")
            return total_stored

        except Exception as e:
            logger.error(f"Error storing chunks: {e}")
            raise

    def search_chunks(
        self,
        query_embedding: List[float],
        case_id: Optional[UUID] = None,
        document_id: Optional[UUID] = None,
        limit: int = 10,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for chunks

        Args:
            query_embedding: Query vector (1024-dim)
            case_id: Filter by case (optional)
            document_id: Filter by document (optional)
            limit: Max results
            score_threshold: Minimum similarity score

        Returns:
            List of matching chunks with scores
        """
        # Build filter
        query_filter = None
        conditions = []

        if case_id:
            conditions.append(
                models.FieldCondition(
                    key="case_id",
                    match=models.MatchValue(value=str(case_id))
                )
            )

        if document_id:
            conditions.append(
                models.FieldCondition(
                    key="document_id",
                    match=models.MatchValue(value=str(document_id))
                )
            )

        if conditions:
            query_filter = models.Filter(must=conditions)

        # Search
        try:
            results = self.client.search(
                collection_name=self.COLLECTION_CHUNKS,
                query_vector=query_embedding,
                query_filter=query_filter,
                limit=limit,
                score_threshold=score_threshold
            )

            chunks = []
            for hit in results:
                chunk = {
                    'chunk_id': hit.payload['chunk_id'],
                    'document_id': UUID(hit.payload['document_id']),
                    'case_id': UUID(hit.payload['case_id']),
                    'page_num': hit.payload['page_num'],
                    'text': hit.payload['text'],
                    'score': hit.score,
                    'char_count': hit.payload['char_count'],
                    # Include metadata for result enhancement
                    'chunk_type': hit.payload.get('chunk_type', 'text'),
                    'temporal_context': hit.payload.get('temporal_context', [])
                }
                chunks.append(chunk)

            logger.info(f"Found {len(chunks)} chunks matching query (threshold={score_threshold})")
            return chunks

        except Exception as e:
            logger.error(f"Error searching chunks: {e}")
            raise

    def get_chunks_by_document(
        self,
        document_id: UUID,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all chunks for a document

        Args:
            document_id: Document UUID
            limit: Max chunks to return

        Returns:
            List of chunks (without embeddings)
        """
        try:
            # Scroll through all matching points
            results = self.client.scroll(
                collection_name=self.COLLECTION_CHUNKS,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(value=str(document_id))
                        )
                    ]
                ),
                limit=limit
            )

            chunks = []
            for point in results[0]:  # results is tuple (points, next_page_offset)
                chunk = {
                    'chunk_id': point.payload['chunk_id'],
                    'page_num': point.payload['page_num'],
                    'chunk_idx': point.payload['chunk_idx'],
                    'text': point.payload['text'],
                    'char_count': point.payload['char_count'],
                    'word_count': point.payload['word_count']
                }
                chunks.append(chunk)

            # Sort by page and chunk index
            chunks.sort(key=lambda x: (x['page_num'], x['chunk_idx']))

            logger.info(f"Retrieved {len(chunks)} chunks for document {document_id}")
            return chunks

        except Exception as e:
            logger.error(f"Error retrieving chunks: {e}")
            raise

    def delete_document_chunks(self, document_id: UUID) -> bool:
        """Delete all chunks for a document"""
        try:
            self.client.delete(
                collection_name=self.COLLECTION_CHUNKS,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="document_id",
                                match=models.MatchValue(value=str(document_id))
                            )
                        ]
                    )
                )
            )
            logger.info(f"Deleted chunks for document {document_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting chunks: {e}")
            return False

    def delete_case_chunks(self, case_id: UUID) -> bool:
        """Delete all chunks for a case"""
        try:
            self.client.delete(
                collection_name=self.COLLECTION_CHUNKS,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="case_id",
                                match=models.MatchValue(value=str(case_id))
                            )
                        ]
                    )
                )
            )
            logger.info(f"Deleted chunks for case {case_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting chunks: {e}")
            return False

    # =========================================================================
    # STATISTICS
    # =========================================================================

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            info = self.client.get_collection(self.COLLECTION_CHUNKS)
            return {
                'collection': self.COLLECTION_CHUNKS,
                'vectors_count': info.vectors_count,
                'indexed_vectors_count': info.indexed_vectors_count,
                'points_count': info.points_count,
                'segments_count': info.segments_count,
                'status': info.status
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {'error': str(e)}

    def get_document_stats(self, document_id: UUID) -> Dict[str, Any]:
        """Get statistics for a specific document"""
        try:
            # Count chunks for document
            results = self.client.count(
                collection_name=self.COLLECTION_CHUNKS,
                count_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(value=str(document_id))
                        )
                    ]
                )
            )

            return {
                'document_id': str(document_id),
                'chunks_count': results.count
            }

        except Exception as e:
            logger.error(f"Error getting document stats: {e}")
            return {'error': str(e)}

    # =========================================================================
    # HEALTH CHECK
    # =========================================================================

    def health_check(self) -> Dict[str, Any]:
        """Check Qdrant health"""
        try:
            collections = self.client.get_collections()
            return {
                'status': 'healthy',
                'collections_count': len(collections.collections),
                'collections': [c.name for c in collections.collections]
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

    def close(self):
        """Close Qdrant connection"""
        if self.client:
            self.client.close()
            logger.info("Qdrant connection closed")
