from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import httpx
from config.config import AUTH_SERVICE_URL

router = APIRouter(prefix="/auth")

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    invite_token: str
    email: str
    password: str

@router.post("/login")
async def login(request: LoginRequest):
    """Proxy login request to auth service."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{AUTH_SERVICE_URL}/login",
                json=request.dict(),
                timeout=30.0
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Auth service unavailable: {str(e)}")

@router.post("/register")
async def register(request: RegisterRequest):
    """Proxy register request to auth service."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{AUTH_SERVICE_URL}/register",
                json=request.dict(),
                timeout=30.0
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Auth service unavailable: {str(e)}")

@router.post("/refresh")
async def refresh_token(refresh_token: str):
    """Proxy refresh token request to auth service."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{AUTH_SERVICE_URL}/refresh",
                json={"refresh_token": refresh_token},
                timeout=30.0
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Auth service unavailable: {str(e)}")