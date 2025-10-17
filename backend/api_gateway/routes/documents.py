from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Request
from pydantic import BaseModel
import httpx
from config.config import DOCUMENT_SERVICE_URL

router = APIRouter(prefix="/policies")

class ApproveDocumentRequest(BaseModel):
    doc_id: str
    action: str  # 'approve' or 'reject'

@router.post("/upload")
async def upload_policies(
    file: UploadFile = File(...),
    authorization: str = Depends(lambda x: x.headers.get("Authorization"))
):
    """Proxy document upload request to document service."""
    async with httpx.AsyncClient() as client:
        try:
            # Prepare files for upload
            files = {
                "file": (file.filename, await file.read(), file.content_type)
            }
            
            # Prepare headers
            headers = {"Authorization": authorization} if authorization else {}
            
            response = await client.post(
                f"{DOCUMENT_SERVICE_URL}/upload",
                files=files,
                headers=headers,
                timeout=60.0  # Longer timeout for file uploads
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Document service unavailable: {str(e)}")

@router.get("/pending")
async def get_pending_documents(
    authorization: str = Depends(lambda x: x.headers.get("Authorization"))
):
    """Proxy get pending documents request to document service."""
    async with httpx.AsyncClient() as client:
        try:
            headers = {"Authorization": authorization} if authorization else {}
            response = await client.get(
                f"{DOCUMENT_SERVICE_URL}/pending",
                headers=headers,
                timeout=30.0
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Document service unavailable: {str(e)}")

@router.post("/approve")
async def approve_document(
    request: ApproveDocumentRequest,
    authorization: str = Depends(lambda x: x.headers.get("Authorization"))
):
    """Proxy approve document request to document service."""
    async with httpx.AsyncClient() as client:
        try:
            headers = {"Authorization": authorization} if authorization else {}
            response = await client.post(
                f"{DOCUMENT_SERVICE_URL}/approve",
                json=request.dict(),
                headers=headers,
                timeout=30.0
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Document service unavailable: {str(e)}")