"""
Elasticsearch Store
Handles full-text search, document discovery, and faceted navigation
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import UUID
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from elasticsearch.exceptions import (
    ConnectionError,
    NotFoundError,
    RequestError,
    TransportError
)

from src.config import settings

logger = logging.getLogger(__name__)


class ElasticStore:
    """Elasticsearch manager for full-text search and document discovery"""

    INDEX_DOCUMENTS = "documents"
    INDEX_METRICS = "financial_metrics"

    def __init__(self):
        self.client = None
        self._connect()
        self._initialize_indexes()

    def _connect(self):
        """Connect to Elasticsearch"""
        try:
            self.client = Elasticsearch(
                hosts=[{
                    'host': settings.elastic_host,
                    'port': settings.elastic_port,
                    'scheme': 'http'
                }],
                timeout=settings.elastic_timeout,
                max_retries=3,
                retry_on_timeout=True
            )

            # Test connection
            if not self.client.ping():
                raise ConnectionError("Cannot ping Elasticsearch server")

            logger.info(f"Connected to Elasticsearch at {settings.elastic_host}:{settings.elastic_port}")

        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {e}")
            logger.warning("Elasticsearch unavailable - search features will be disabled")
            self.client = None

    def _initialize_indexes(self):
        """Create indexes if they don't exist"""
        if not self.client:
            logger.warning("Skipping index initialization - Elasticsearch not connected")
            return

        try:
            # Documents index mapping
            documents_mapping = {
                "mappings": {
                    "properties": {
                        "document_id": {"type": "keyword"},
                        "case_id": {"type": "keyword"},
                        "filename": {
                            "type": "text",
                            "fields": {
                                "keyword": {"type": "keyword"}
                            }
                        },
                        "original_filename": {
                            "type": "text",
                            "fields": {
                                "keyword": {"type": "keyword"}
                            }
                        },
                        "content": {
                            "type": "text",
                            "analyzer": "standard"
                        },
                        "document_type": {"type": "keyword"},
                        "mime_type": {"type": "keyword"},
                        "page_count": {"type": "integer"},
                        "file_size": {"type": "long"},
                        "status": {"type": "keyword"},
                        "created_at": {"type": "date"},
                        "processed_at": {"type": "date"},
                        "metadata": {"type": "object", "enabled": False}
                    }
                },
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "analysis": {
                        "analyzer": {
                            "default": {
                                "type": "standard"
                            }
                        }
                    }
                }
            }

            # Metrics index mapping
            metrics_mapping = {
                "mappings": {
                    "properties": {
                        "metric_id": {"type": "keyword"},
                        "document_id": {"type": "keyword"},
                        "case_id": {"type": "keyword"},
                        "metric_name": {
                            "type": "text",
                            "fields": {
                                "keyword": {"type": "keyword"}
                            }
                        },
                        "metric_value": {"type": "double"},
                        "metric_unit": {"type": "keyword"},
                        "fiscal_year": {"type": "integer"},
                        "fiscal_period": {"type": "keyword"},
                        "page_number": {"type": "integer"},
                        "confidence": {"type": "float"},
                        "calculation_method": {"type": "keyword"},
                        "created_at": {"type": "date"}
                    }
                },
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0
                }
            }

            # Create documents index
            if not self.client.indices.exists(index=self.INDEX_DOCUMENTS):
                self.client.indices.create(
                    index=self.INDEX_DOCUMENTS,
                    body=documents_mapping
                )
                logger.info(f"Created index: {self.INDEX_DOCUMENTS}")
            else:
                logger.info(f"Index {self.INDEX_DOCUMENTS} already exists")

            # Create metrics index
            if not self.client.indices.exists(index=self.INDEX_METRICS):
                self.client.indices.create(
                    index=self.INDEX_METRICS,
                    body=metrics_mapping
                )
                logger.info(f"Created index: {self.INDEX_METRICS}")
            else:
                logger.info(f"Index {self.INDEX_METRICS} already exists")

        except Exception as e:
            logger.error(f"Failed to initialize indexes: {e}")
            raise

    # =========================================================================
    # DOCUMENT OPERATIONS
    # =========================================================================

    def index_document(
        self,
        doc_id: UUID,
        content: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Index a single document

        Args:
            doc_id: Document UUID
            content: Full text content
            metadata: Document metadata (filename, case_id, etc.)

        Returns:
            True if indexed successfully
        """
        if not self.client:
            logger.warning("Elasticsearch not available - skipping indexing")
            return False

        try:
            document = {
                "document_id": str(doc_id),
                "case_id": str(metadata.get('case_id', '')),
                "filename": metadata.get('filename', ''),
                "original_filename": metadata.get('original_filename', ''),
                "content": content,
                "document_type": metadata.get('document_type', 'financial'),
                "mime_type": metadata.get('mime_type', 'application/pdf'),
                "page_count": metadata.get('page_count'),
                "file_size": metadata.get('file_size'),
                "status": metadata.get('status', 'indexed'),
                "created_at": metadata.get('created_at', datetime.now()).isoformat(),
                "processed_at": datetime.now().isoformat(),
                "metadata": metadata.get('extra_metadata', {})
            }

            self.client.index(
                index=self.INDEX_DOCUMENTS,
                id=str(doc_id),
                document=document
            )

            logger.info(f"Indexed document: {doc_id}")
            return True

        except Exception as e:
            logger.error(f"Error indexing document {doc_id}: {e}")
            return False

    def bulk_index_documents(self, documents: List[Dict[str, Any]]) -> int:
        """
        Bulk index multiple documents

        Args:
            documents: List of dicts with doc_id, content, metadata

        Returns:
            Number of documents successfully indexed
        """
        if not self.client:
            logger.warning("Elasticsearch not available - skipping bulk indexing")
            return 0

        if not documents:
            return 0

        try:
            actions = []
            for doc in documents:
                action = {
                    "_index": self.INDEX_DOCUMENTS,
                    "_id": str(doc['doc_id']),
                    "_source": {
                        "document_id": str(doc['doc_id']),
                        "case_id": str(doc['metadata'].get('case_id', '')),
                        "filename": doc['metadata'].get('filename', ''),
                        "original_filename": doc['metadata'].get('original_filename', ''),
                        "content": doc['content'],
                        "document_type": doc['metadata'].get('document_type', 'financial'),
                        "mime_type": doc['metadata'].get('mime_type', 'application/pdf'),
                        "page_count": doc['metadata'].get('page_count'),
                        "file_size": doc['metadata'].get('file_size'),
                        "status": doc['metadata'].get('status', 'indexed'),
                        "created_at": doc['metadata'].get('created_at', datetime.now()).isoformat(),
                        "processed_at": datetime.now().isoformat(),
                        "metadata": doc['metadata'].get('extra_metadata', {})
                    }
                }
                actions.append(action)

            success, failed = bulk(self.client, actions, raise_on_error=False)

            logger.info(f"Bulk indexed {success} documents ({failed} failed)")
            return success

        except Exception as e:
            logger.error(f"Error in bulk indexing: {e}")
            return 0

    def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        offset: int = 0,
        highlight: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Full-text search across documents

        Args:
            query: Search query string
            filters: Optional filters (case_id, document_type, date_range)
            limit: Max results to return
            offset: Pagination offset
            highlight: Whether to highlight matching terms

        Returns:
            List of matching documents with scores
        """
        if not self.client:
            logger.warning("Elasticsearch not available - returning empty results")
            return []

        try:
            # Build query
            must_clauses = []

            # Multi-match across fields
            if query:
                must_clauses.append({
                    "multi_match": {
                        "query": query,
                        "fields": [
                            "content^3",  # Boost content matches
                            "filename^2",
                            "original_filename^2"
                        ],
                        "type": "best_fields",
                        "operator": "or"
                    }
                })

            # Apply filters
            filter_clauses = []
            if filters:
                if 'case_id' in filters:
                    filter_clauses.append({
                        "term": {"case_id": str(filters['case_id'])}
                    })

                if 'document_type' in filters:
                    filter_clauses.append({
                        "term": {"document_type": filters['document_type']}
                    })

                if 'status' in filters:
                    filter_clauses.append({
                        "term": {"status": filters['status']}
                    })

                if 'date_from' in filters or 'date_to' in filters:
                    date_range = {}
                    if 'date_from' in filters:
                        date_range['gte'] = filters['date_from']
                    if 'date_to' in filters:
                        date_range['lte'] = filters['date_to']

                    filter_clauses.append({
                        "range": {"created_at": date_range}
                    })

            # Construct full query
            search_query = {
                "bool": {
                    "must": must_clauses if must_clauses else [{"match_all": {}}],
                    "filter": filter_clauses
                }
            }

            # Build search body
            search_body = {
                "query": search_query,
                "from": offset,
                "size": limit,
                "sort": [
                    {"_score": {"order": "desc"}},
                    {"created_at": {"order": "desc"}}
                ]
            }

            # Add highlighting
            if highlight and query:
                search_body["highlight"] = {
                    "fields": {
                        "content": {
                            "fragment_size": 150,
                            "number_of_fragments": 3
                        },
                        "filename": {},
                        "original_filename": {}
                    },
                    "pre_tags": ["<mark>"],
                    "post_tags": ["</mark>"]
                }

            # Execute search
            response = self.client.search(
                index=self.INDEX_DOCUMENTS,
                body=search_body
            )

            # Parse results
            results = []
            for hit in response['hits']['hits']:
                result = {
                    'document_id': UUID(hit['_source']['document_id']),
                    'case_id': UUID(hit['_source']['case_id']) if hit['_source']['case_id'] else None,
                    'filename': hit['_source']['filename'],
                    'original_filename': hit['_source']['original_filename'],
                    'document_type': hit['_source']['document_type'],
                    'page_count': hit['_source'].get('page_count'),
                    'created_at': hit['_source']['created_at'],
                    'score': hit['_score']
                }

                # Add highlights if available
                if 'highlight' in hit:
                    result['highlights'] = hit['highlight']

                results.append(result)

            logger.info(f"Search returned {len(results)} results for query: '{query}'")
            return results

        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []

    def search_with_aggregations(
        self,
        query: str,
        agg_fields: List[str],
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Faceted search with aggregations

        Args:
            query: Search query string
            agg_fields: Fields to aggregate (e.g., ['document_type', 'status'])
            filters: Optional filters

        Returns:
            Dict with results and aggregations
        """
        if not self.client:
            logger.warning("Elasticsearch not available - returning empty results")
            return {"results": [], "aggregations": {}}

        try:
            # Build base query (same as search method)
            must_clauses = []
            if query:
                must_clauses.append({
                    "multi_match": {
                        "query": query,
                        "fields": ["content^3", "filename^2", "original_filename^2"],
                        "type": "best_fields"
                    }
                })

            filter_clauses = []
            if filters:
                if 'case_id' in filters:
                    filter_clauses.append({"term": {"case_id": str(filters['case_id'])}})
                if 'document_type' in filters:
                    filter_clauses.append({"term": {"document_type": filters['document_type']}})

            search_query = {
                "bool": {
                    "must": must_clauses if must_clauses else [{"match_all": {}}],
                    "filter": filter_clauses
                }
            }

            # Build aggregations
            aggs = {}
            for field in agg_fields:
                aggs[f"{field}_facet"] = {
                    "terms": {
                        "field": field if field in ['document_type', 'status', 'mime_type'] else f"{field}.keyword",
                        "size": 50
                    }
                }

            # Execute search with aggregations
            response = self.client.search(
                index=self.INDEX_DOCUMENTS,
                body={
                    "query": search_query,
                    "size": 0,  # We only want aggregations
                    "aggs": aggs
                }
            )

            # Parse aggregations
            aggregations = {}
            for agg_name, agg_data in response['aggregations'].items():
                field_name = agg_name.replace('_facet', '')
                aggregations[field_name] = [
                    {"value": bucket['key'], "count": bucket['doc_count']}
                    for bucket in agg_data['buckets']
                ]

            result = {
                "total_hits": response['hits']['total']['value'],
                "aggregations": aggregations
            }

            logger.info(f"Faceted search returned {result['total_hits']} total hits")
            return result

        except Exception as e:
            logger.error(f"Error in faceted search: {e}")
            return {"results": [], "aggregations": {}}

    def delete_document(self, doc_id: UUID) -> bool:
        """Delete document from index"""
        if not self.client:
            logger.warning("Elasticsearch not available - skipping deletion")
            return False

        try:
            self.client.delete(
                index=self.INDEX_DOCUMENTS,
                id=str(doc_id)
            )
            logger.info(f"Deleted document: {doc_id}")
            return True

        except NotFoundError:
            logger.warning(f"Document not found: {doc_id}")
            return False
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False

    def delete_by_case(self, case_id: UUID) -> int:
        """
        Delete all documents for a case

        Returns:
            Number of documents deleted
        """
        if not self.client:
            logger.warning("Elasticsearch not available - skipping deletion")
            return 0

        try:
            response = self.client.delete_by_query(
                index=self.INDEX_DOCUMENTS,
                body={
                    "query": {
                        "term": {"case_id": str(case_id)}
                    }
                }
            )

            deleted = response.get('deleted', 0)
            logger.info(f"Deleted {deleted} documents for case {case_id}")
            return deleted

        except Exception as e:
            logger.error(f"Error deleting documents by case: {e}")
            return 0

    # =========================================================================
    # HEALTH CHECK
    # =========================================================================

    def health_check(self) -> Dict[str, Any]:
        """Check Elasticsearch cluster health"""
        if not self.client:
            return {
                "status": "unavailable",
                "error": "Elasticsearch client not connected"
            }

        try:
            # Get cluster health
            health = self.client.cluster.health()

            # Get index stats
            stats = {}
            for index_name in [self.INDEX_DOCUMENTS, self.INDEX_METRICS]:
                if self.client.indices.exists(index=index_name):
                    index_stats = self.client.indices.stats(index=index_name)
                    stats[index_name] = {
                        "docs_count": index_stats['_all']['primaries']['docs']['count'],
                        "size_bytes": index_stats['_all']['primaries']['store']['size_in_bytes']
                    }

            return {
                "status": health['status'],
                "cluster_name": health['cluster_name'],
                "number_of_nodes": health['number_of_nodes'],
                "active_shards": health['active_shards'],
                "indexes": stats
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    def close(self):
        """Close Elasticsearch connection"""
        if self.client:
            self.client.close()
            logger.info("Elasticsearch connection closed")
