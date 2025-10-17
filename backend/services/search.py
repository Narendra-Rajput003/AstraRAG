import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from elasticsearch import Elasticsearch, NotFoundError
from config.config import ELASTICSEARCH_URL, ELASTICSEARCH_INDEX

logger = logging.getLogger(__name__)

class DocumentSearchService:
    def __init__(self):
        self.es = Elasticsearch(ELASTICSEARCH_URL)
        self.index_name = ELASTICSEARCH_INDEX
        self._ensure_index()
        self._search_cache = {}  # Simple in-memory cache for search results
        self._cache_max_size = 100
        self._cache_ttl = 300  # 5 minutes TTL

    def _get_cache_key(self, query: str, filters: Dict[str, Any],
                       sort_by: str, sort_order: str, page: int, size: int) -> str:
        """Generate a cache key for search parameters."""
        filter_str = str(sorted(filters.items())) if filters else ""
        return f"{query}|{filter_str}|{sort_by}|{sort_order}|{page}|{size}"

    def _get_cached_result(self, cache_key: str) -> Optional[Dict]:
        """Get cached result if it exists and hasn't expired."""
        if cache_key in self._search_cache:
            cached_item = self._search_cache[cache_key]
            if time.time() - cached_item['timestamp'] < self._cache_ttl:
                logger.info(f"Search cache hit for key: {cache_key}")
                return cached_item['result']
            else:
                # Remove expired cache entry
                del self._search_cache[cache_key]
        return None

    def _set_cached_result(self, cache_key: str, result: Dict):
        """Cache search result."""
        # Implement LRU-style cache eviction
        if len(self._search_cache) >= self._cache_max_size:
            # Remove oldest entry
            oldest_key = min(self._search_cache.keys(),
                           key=lambda k: self._search_cache[k]['timestamp'])
            del self._search_cache[oldest_key]

        self._search_cache[cache_key] = {
            'result': result,
            'timestamp': time.time()
        }
        logger.info(f"Cached search result for key: {cache_key}")

    def _clear_document_cache(self, doc_id: str):
        """Clear cache entries that might contain the updated/deleted document."""
        # For simplicity, clear all cache when a document is modified
        # In production, you might want more sophisticated cache invalidation
        cache_size_before = len(self._search_cache)
        self._search_cache.clear()
        logger.info(f"Cleared search cache due to document {doc_id} modification (was {cache_size_before} entries)")

    def _ensure_index(self):
        """Create index with proper mappings if it doesn't exist."""
        if not self.es.indices.exists(index=self.index_name):
            mapping = {
                "mappings": {
                    "properties": {
                        "doc_id": {"type": "keyword"},
                        "filename": {"type": "text", "analyzer": "standard"},
                        "content": {"type": "text", "analyzer": "standard"},
                        "uploaded_by": {"type": "keyword"},
                        "uploaded_at": {"type": "date"},
                        "file_type": {"type": "keyword"},
                        "file_size": {"type": "long"},
                        "status": {"type": "keyword"},
                        "metadata": {
                            "type": "object",
                            "dynamic": True
                        },
                        "tags": {"type": "keyword"},
                        "chunks": {
                            "type": "nested",
                            "properties": {
                                "chunk_id": {"type": "keyword"},
                                "content": {"type": "text", "analyzer": "standard"},
                                "chunk_index": {"type": "integer"},
                                "metadata": {"type": "object", "dynamic": True}
                            }
                        }
                    }
                },
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "analysis": {
                        "analyzer": {
                            "standard": {
                                "type": "standard",
                                "stopwords": "_english_"
                            }
                        }
                    }
                }
            }
            self.es.indices.create(index=self.index_name, body=mapping)
            logger.info(f"Created Elasticsearch index: {self.index_name}")

    def index_document(self, doc_id: str, filename: str, content: str,
                      uploaded_by: str, uploaded_at: str, file_type: str,
                      file_size: int, status: str, metadata: Dict[str, Any],
                      tags: List[str] = None, chunks: List[Dict] = None) -> bool:
        """Index a document in Elasticsearch."""
        try:
            doc = {
                "doc_id": doc_id,
                "filename": filename,
                "content": content,
                "uploaded_by": uploaded_by,
                "uploaded_at": uploaded_at,
                "file_type": file_type,
                "file_size": file_size,
                "status": status,
                "metadata": metadata,
                "tags": tags or []
            }

            if chunks:
                doc["chunks"] = chunks

            response = self.es.index(index=self.index_name, id=doc_id, document=doc)
            logger.info(f"Indexed document {doc_id}: {response['result']}")
            return True
        except Exception as e:
            logger.error(f"Failed to index document {doc_id}: {e}")
            return False

    def search_documents(self, query: str, filters: Dict[str, Any] = None,
                        sort_by: str = "uploaded_at", sort_order: str = "desc",
                        page: int = 1, size: int = 20) -> Tuple[List[Dict], int]:
        """Search documents with faceted filtering, caching, and performance monitoring."""
        start_time = time.time()

        # Generate cache key
        cache_key = self._get_cache_key(query, filters or {}, sort_by, sort_order, page, size)

        # Check cache first (only for non-empty queries to avoid caching empty results)
        if query.strip():
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                end_time = time.time()
                logger.info(f"Cached search completed in {end_time - start_time:.3f}s")
                return cached_result, cached_result["total"]

        try:
            # Build query
            es_query = {"bool": {"must": [], "filter": []}}

            # Full-text search
            if query:
                es_query["bool"]["must"].append({
                    "multi_match": {
                        "query": query,
                        "fields": ["filename^2", "content", "tags"],
                        "fuzziness": "AUTO"
                    }
                })

            # Apply filters
            if filters:
                for field, value in filters.items():
                    if field == "file_type" and value:
                        es_query["bool"]["filter"].append({"term": {"file_type": value}})
                    elif field == "uploaded_by" and value:
                        es_query["bool"]["filter"].append({"term": {"uploaded_by": value}})
                    elif field == "status" and value:
                        es_query["bool"]["filter"].append({"term": {"status": value}})
                    elif field == "tags" and value:
                        es_query["bool"]["filter"].append({"terms": {"tags": value}})
                    elif field == "date_from" and value:
                        es_query["bool"]["filter"].append({
                            "range": {"uploaded_at": {"gte": value}}
                        })
                    elif field == "date_to" and value:
                        es_query["bool"]["filter"].append({
                            "range": {"uploaded_at": {"lte": value}}
                        })
                    elif field == "file_size_min" and value:
                        es_query["bool"]["filter"].append({
                            "range": {"file_size": {"gte": value}}
                        })
                    elif field == "file_size_max" and value:
                        es_query["bool"]["filter"].append({
                            "range": {"file_size": {"lte": value}}
                        })
                    elif field.startswith("metadata.") and value:
                        metadata_field = field.replace("metadata.", "")
                        es_query["bool"]["filter"].append({
                            "term": {f"metadata.{metadata_field}": value}
                        })

            # Build search request
            search_body = {
                "query": es_query,
                "sort": [{sort_by: {"order": sort_order}}],
                "from": (page - 1) * size,
                "size": size,
                "track_total_hits": True
            }

            # Add aggregations for facets
            search_body["aggs"] = {
                "file_types": {"terms": {"field": "file_type"}},
                "uploaders": {"terms": {"field": "uploaded_by"}},
                "statuses": {"terms": {"field": "status"}},
                "tags": {"terms": {"field": "tags"}},
                "date_histogram": {
                    "date_histogram": {
                        "field": "uploaded_at",
                        "calendar_interval": "month",
                        "format": "yyyy-MM"
                    }
                }
            }

            response = self.es.search(index=self.index_name, body=search_body)

            # Process results
            hits = response["hits"]["hits"]
            total = response["hits"]["total"]["value"] if isinstance(response["hits"]["total"], dict) else response["hits"]["total"]

            documents = []
            for hit in hits:
                doc = hit["_source"]
                doc["_score"] = hit["_score"]
                documents.append(doc)

            # Process aggregations
            aggregations = response.get("aggregations", {})
            facets = {
                "file_types": [bucket["key"] for bucket in aggregations.get("file_types", {}).get("buckets", [])],
                "uploaders": [bucket["key"] for bucket in aggregations.get("uploaders", {}).get("buckets", [])],
                "statuses": [bucket["key"] for bucket in aggregations.get("statuses", {}).get("buckets", [])],
                "tags": [bucket["key"] for bucket in aggregations.get("tags", {}).get("buckets", [])],
                "date_ranges": [
                    {"key": bucket["key_as_string"], "count": bucket["doc_count"]}
                    for bucket in aggregations.get("date_histogram", {}).get("buckets", [])
                ]
            }

            # Add facets to response
            result = {
                "documents": documents,
                "total": total,
                "page": page,
                "size": size,
                "facets": facets
            }

            # Cache the result for future queries
            if query.strip():
                self._set_cached_result(cache_key, result)

            # Performance logging
            end_time = time.time()
            duration = end_time - start_time
            logger.info(f"Search completed in {duration:.3f}s - Query: '{query}' - Results: {total} - Page: {page}")

            # Performance warning for slow queries
            if duration > 2.0:
                logger.warning(f"Slow search query detected: {duration:.3f}s - Query: '{query}' - Filters: {filters}")

            return result, total

        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            logger.error(f"Search failed after {duration:.3f}s: {e}")
            return {"documents": [], "total": 0, "page": page, "size": size, "facets": {}}, 0

    def update_document(self, doc_id: str, updates: Dict[str, Any]) -> bool:
        """Update a document in the index."""
        try:
            response = self.es.update(index=self.index_name, id=doc_id,
                                    doc=updates, doc_as_upsert=True)
            logger.info(f"Updated document {doc_id}: {response['result']}")

            # Clear related cache entries when document is updated
            self._clear_document_cache(doc_id)

            return True
        except NotFoundError:
            logger.warning(f"Document {doc_id} not found for update")
            return False
        except Exception as e:
            logger.error(f"Failed to update document {doc_id}: {e}")
            return False

    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the index."""
        try:
            response = self.es.delete(index=self.index_name, id=doc_id)
            logger.info(f"Deleted document {doc_id}: {response['result']}")

            # Clear related cache entries when document is deleted
            self._clear_document_cache(doc_id)

            return True
        except NotFoundError:
            logger.warning(f"Document {doc_id} not found for deletion")
            return False
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            return False

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific document by ID."""
        try:
            response = self.es.get(index=self.index_name, id=doc_id)
            return response["_source"]
        except NotFoundError:
            return None
        except Exception as e:
            logger.error(f"Failed to get document {doc_id}: {e}")
            return None

# Global instance
search_service = DocumentSearchService()