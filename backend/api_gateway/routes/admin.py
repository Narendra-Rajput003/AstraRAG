from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional
import httpx
from config.config import ADMIN_SERVICE_URL

router = APIRouter(prefix="/admin")

class InviteRequest(BaseModel):
    email: str
    role: str

class ApproveDocumentRequest(BaseModel):
    doc_id: str
    action: str  # 'approve' or 'reject'

class MFASetupRequest(BaseModel):
    code: str

class MFAVerifyRequest(BaseModel):
    code: str

@router.post("/invite")
async def create_user_invite(
    request: InviteRequest,
    authorization: str = Depends(lambda x: x.headers.get("Authorization"))
):
    """Proxy create user invite request to admin service."""
    async with httpx.AsyncClient() as client:
        try:
            headers = {"Authorization": authorization} if authorization else {}
            response = await client.post(
                f"{ADMIN_SERVICE_URL}/invite",
                json=request.dict(),
                headers=headers,
                timeout=30.0
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Admin service unavailable: {str(e)}")

@router.get("/invites")
async def list_invites(
    authorization: str = Depends(lambda x: x.headers.get("Authorization"))
):
    """Proxy list invites request to admin service."""
    async with httpx.AsyncClient() as client:
        try:
            headers = {"Authorization": authorization} if authorization else {}
            response = await client.get(
                f"{ADMIN_SERVICE_URL}/invites",
                headers=headers,
                timeout=30.0
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Admin service unavailable: {str(e)}")

@router.post("/revoke-invite/{invite_id}")
async def revoke_invite(
    invite_id: str,
    authorization: str = Depends(lambda x: x.headers.get("Authorization"))
):
    """Proxy revoke invite request to admin service."""
    async with httpx.AsyncClient() as client:
        try:
            headers = {"Authorization": authorization} if authorization else {}
            response = await client.post(
                f"{ADMIN_SERVICE_URL}/revoke-invite/{invite_id}",
                headers=headers,
                timeout=30.0
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Admin service unavailable: {str(e)}")

@router.get("/documents/pending")
async def get_pending_documents(
    authorization: str = Depends(lambda x: x.headers.get("Authorization"))
):
    """Proxy get pending documents request to admin service."""
    async with httpx.AsyncClient() as client:
        try:
            headers = {"Authorization": authorization} if authorization else {}
            response = await client.get(
                f"{ADMIN_SERVICE_URL}/documents/pending",
                headers=headers,
                timeout=30.0
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Admin service unavailable: {str(e)}")

@router.post("/documents/approve")
async def approve_document(
    request: ApproveDocumentRequest,
    authorization: str = Depends(lambda x: x.headers.get("Authorization"))
):
    """Proxy approve document request to admin service."""
    async with httpx.AsyncClient() as client:
        try:
            headers = {"Authorization": authorization} if authorization else {}
            response = await client.post(
                f"{ADMIN_SERVICE_URL}/documents/approve",
                json=request.dict(),
                headers=headers,
                timeout=30.0
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Admin service unavailable: {str(e)}")

@router.get("/users")
async def get_users(
    authorization: str = Depends(lambda x: x.headers.get("Authorization"))
):
    """Proxy get users request to admin service."""
    async with httpx.AsyncClient() as client:
        try:
            headers = {"Authorization": authorization} if authorization else {}
            response = await client.get(
                f"{ADMIN_SERVICE_URL}/users",
                headers=headers,
                timeout=30.0
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Admin service unavailable: {str(e)}")

@router.post("/mfa/setup")
async def setup_user_mfa(
    authorization: str = Depends(lambda x: x.headers.get("Authorization"))
):
    """Proxy setup MFA request to admin service."""
    async with httpx.AsyncClient() as client:
        try:
            headers = {"Authorization": authorization} if authorization else {}
            response = await client.post(
                f"{ADMIN_SERVICE_URL}/mfa/setup",
                headers=headers,
                timeout=30.0
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Admin service unavailable: {str(e)}")

@router.post("/mfa/verify")
async def verify_user_mfa(
    request: MFAVerifyRequest,
    authorization: str = Depends(lambda x: x.headers.get("Authorization"))
):
    """Proxy verify MFA request to admin service."""
    async with httpx.AsyncClient() as client:
        try:
            headers = {"Authorization": authorization} if authorization else {}
            response = await client.post(
                f"{ADMIN_SERVICE_URL}/mfa/verify",
                json=request.dict(),
                headers=headers,
                timeout=30.0
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Admin service unavailable: {str(e)}")

@router.get("/security-audit")
async def run_security_audit(
    authorization: str = Depends(lambda x: x.headers.get("Authorization"))
):
    """Proxy run security audit request to admin service."""
    async with httpx.AsyncClient() as client:
        try:
            headers = {"Authorization": authorization} if authorization else {}
            response = await client.get(
                f"{ADMIN_SERVICE_URL}/security-audit",
                headers=headers,
                timeout=30.0
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Admin service unavailable: {str(e)}")

@router.get("/security-audit/summary")
async def get_security_audit_summary(
    authorization: str = Depends(lambda x: x.headers.get("Authorization"))
):
    """Proxy get security audit summary request to admin service."""
    async with httpx.AsyncClient() as client:
        try:
            headers = {"Authorization": authorization} if authorization else {}
            response = await client.get(
                f"{ADMIN_SERVICE_URL}/security-audit/summary",
                headers=headers,
                timeout=30.0
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Admin service unavailable: {str(e)}")