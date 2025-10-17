from fastapi import APIRouter, HTTPException, Depends, Request, Response
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import httpx
from config.config import SEARCH_SERVICE_URL
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/search")

class SearchRequest(BaseModel):
    query: str = ""
    filters: Optional[Dict[str, Any]] = None
    sort_by: str = "uploaded_at"
    sort_order: str = "desc"
    page: int = 1
    size: int = 20

class QueryRequest(BaseModel):
    query: str
    token: Optional[str] = None

@router.post("/documents")
async def search_documents(
    request: SearchRequest,
    authorization: str = Depends(lambda x: x.headers.get("Authorization"))
):
    """Proxy search documents request to search service."""
    async with httpx.AsyncClient() as client:
        try:
            headers = {"Authorization": authorization} if authorization else {}
            response = await client.post(
                f"{SEARCH_SERVICE_URL}/documents",
                json=request.dict(),
                headers=headers,
                timeout=30.0
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Search service unavailable: {str(e)}")

@router.get("/facets")
async def get_search_facets(
    authorization: str = Depends(lambda x: x.headers.get("Authorization"))
):
    """Proxy get search facets request to search service."""
    async with httpx.AsyncClient() as client:
        try:
            headers = {"Authorization": authorization} if authorization else {}
            response = await client.get(
                f"{SEARCH_SERVICE_URL}/facets",
                headers=headers,
                timeout=30.0
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Search service unavailable: {str(e)}")

@router.post("/ask")
async def query_rag(
    request: QueryRequest,
    authorization: str = Depends(lambda x: x.headers.get("Authorization"))
):
    """Proxy QA query request to search service and stream the response through to the client."""
    headers = {"Authorization": authorization} if authorization else {}

    try:
        async with httpx.AsyncClient(timeout=None) as client:
            # Use stream to forward bytes as they arrive
            async with client.stream("POST", f"{SEARCH_SERVICE_URL}/ask", json=request.dict(), headers=headers) as resp:
                # If backend returned error status, read body and forward as HTTPException
                if resp.status_code >= 400:
                    text = await resp.aread()
                    raise HTTPException(status_code=502, detail=f"Search service error: {resp.status_code} {text.decode(errors='ignore')}")

                # Preserve content-type if present
                content_type = resp.headers.get("content-type", "text/plain; charset=utf-8")

                async def stream_generator():
                    async for chunk in resp.aiter_bytes():
                        if not chunk:
                            continue
                        yield chunk

                return StreamingResponse(stream_generator(), media_type=content_type)

    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Search service unavailable: {str(e)}")