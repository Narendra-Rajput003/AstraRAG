from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any
import httpx
from config.config import ANALYTICS_SERVICE_URL

router = APIRouter(prefix="/analytics")

class TrackEventRequest(BaseModel):
    event_type: str
    event_data: Optional[Dict[str, Any]] = None

@router.get("/user-activity")
async def get_user_activity(
    days: int = 30,
    authorization: str = Depends(lambda x: x.headers.get("Authorization"))
):
    """Proxy get user activity request to analytics service."""
    async with httpx.AsyncClient() as client:
        try:
            headers = {"Authorization": authorization} if authorization else {}
            response = await client.get(
                f"{ANALYTICS_SERVICE_URL}/user-activity?days={days}",
                headers=headers,
                timeout=30.0
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Analytics service unavailable: {str(e)}")

@router.get("/system-metrics")
async def get_system_metrics(
    hours: int = 24,
    authorization: str = Depends(lambda x: x.headers.get("Authorization"))
):
    """Proxy get system metrics request to analytics service."""
    async with httpx.AsyncClient() as client:
        try:
            headers = {"Authorization": authorization} if authorization else {}
            response = await client.get(
                f"{ANALYTICS_SERVICE_URL}/system-metrics?hours={hours}",
                headers=headers,
                timeout=30.0
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Analytics service unavailable: {str(e)}")

@router.post("/track")
async def track_analytics_event(
    request: TrackEventRequest,
    authorization: str = Depends(lambda x: x.headers.get("Authorization"))
):
    """Proxy track analytics event request to analytics service."""
    async with httpx.AsyncClient() as client:
        try:
            headers = {"Authorization": authorization} if authorization else {}
            response = await client.post(
                f"{ANALYTICS_SERVICE_URL}/track",
                json=request.dict(),
                headers=headers,
                timeout=30.0
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Analytics service unavailable: {str(e)}")