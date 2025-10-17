import sys
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any, Tuple, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

# Add project root to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.search import search_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchRequest(BaseModel):
    query: str = ""
    filters: Optional[Dict[str, Any]] = None
    sort_by: str = "uploaded_at"
    sort_order: str = "desc"
    page: int = 1
    size: int = 20

class SearchResponse(BaseModel):
    documents: List[Dict[str, Any]]
    total: int
    page: int
    size: int
    facets: Dict[str, Any]

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Search service startup")
    yield
    logger.info("Search service shutdown")

app = FastAPI(
    title="Search Service",
    description="Document search and indexing microservice",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "search-service",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/search/documents")
async def search_documents(request: SearchRequest, req: Request = None):
    """Advanced search with faceted filtering."""
    user_id = req.headers.get("X-User-ID") if req else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    try:
        result, total = search_service.search_documents(
            query=request.query,
            filters=request.filters,
            sort_by=request.sort_by,
            sort_order=request.sort_order,
            page=request.page,
            size=request.size
        )

        return SearchResponse(**result)

    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@app.get("/search/facets")
async def get_search_facets(req: Request = None):
    """Get available search facets."""
    user_id = req.headers.get("X-User-ID") if req else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    try:
        # Get all documents for facet calculation
        result, _ = search_service.search_documents(query="", page=1, size=10000)
        return result.get("facets", {})

    except Exception as e:
        logger.error(f"Facets error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get facets")

@app.post("/index/document")
async def index_document(
    doc_id: str,
    filename: str,
    content: str,
    uploaded_by: str,
    uploaded_at: str,
    file_type: str,
    file_size: int,
    status: str,
    metadata: Dict[str, Any],
    tags: Optional[List[str]] = None,
    req: Request = None
):
    """Index a document (called by document service)."""
    # This endpoint is for inter-service communication
    # In production, add proper service authentication

    try:
        success = search_service.index_document(
            doc_id=doc_id,
            filename=filename,
            content=content,
            uploaded_by=uploaded_by,
            uploaded_at=uploaded_at,
            file_type=file_type,
            file_size=file_size,
            status=status,
            metadata=metadata,
            tags=tags
        )

        if success:
            return {"message": "Document indexed successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to index document")

    except Exception as e:
        logger.error(f"Indexing error for document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Indexing failed")

@app.put("/index/document/{doc_id}")
async def update_document_index(
    doc_id: str,
    updates: Dict[str, Any],
    req: Request = None
):
    """Update document in index (called by document service)."""
    try:
        success = search_service.update_document(doc_id, updates)

        if success:
            return {"message": "Document updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Document not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update error for document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Update failed")

@app.delete("/index/document/{doc_id}")
async def delete_document_index(doc_id: str, req: Request = None):
    """Delete document from index (called by document service)."""
    try:
        success = search_service.delete_document(doc_id)

        if success:
            return {"message": "Document deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Document not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete error for document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Delete failed")

@app.get("/index/stats")
async def get_index_stats(req: Request = None):
    """Get search index statistics."""
    try:
        # Get basic index stats
        index_name = search_service.index_name
        es = search_service.es

        stats = es.indices.stats(index=index_name)
        health = es.cluster.health()

        return {
            "index_name": index_name,
            "document_count": stats["indices"][index_name]["total"]["docs"]["count"],
            "index_size": stats["indices"][index_name]["total"]["store"]["size_in_bytes"],
            "cluster_status": health["status"],
            "active_shards": health["active_shards"]
        }

    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get index stats")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)