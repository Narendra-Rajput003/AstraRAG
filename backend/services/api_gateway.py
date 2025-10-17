import sys
import os
import logging
import time
import json
import httpx
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.config import JWT_SECRET, REDIS_URL, REDIS_TOKEN
from backend.auth import require_auth, require_role

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Service URLs from environment
SERVICE_URLS = {
    'auth': os.getenv('AUTH_SERVICE_URL', 'http://localhost:8001'),
    'document': os.getenv('DOCUMENT_SERVICE_URL', 'http://localhost:8002'),
    'search': os.getenv('SEARCH_SERVICE_URL', 'http://localhost:8003'),
    'analytics': os.getenv('ANALYTICS_SERVICE_URL', 'http://localhost:8004'),
    'admin': os.getenv('ADMIN_SERVICE_URL', 'http://localhost:8005'),
}

# Route mappings: endpoint -> service
ROUTE_MAPPINGS = {
    # Auth service routes
    '/auth/login': 'auth',
    '/auth/register': 'auth',
    '/auth/mfa/setup': 'auth',
    '/auth/mfa/verify': 'auth',
    '/auth/mfa/authenticate': 'auth',
    '/auth/mfa/complete-login': 'auth',
    '/auth/validate': 'auth',
    '/admin/invite': 'auth',
    '/admin/invites': 'auth',
    '/admin/revoke-invite': 'auth',

    # Document service routes
    '/policies/upload': 'document',
    '/admin/documents/pending': 'document',
    '/admin/documents/approve': 'document',
    '/documents/': 'document',  # All document-related routes

    # Search service routes
    '/search/documents': 'search',
    '/search/facets': 'search',

    # Analytics service routes
    '/analytics/user-activity': 'analytics',
    '/analytics/system-metrics': 'analytics',
    '/analytics/track': 'analytics',

    # Admin service routes
    '/admin/security-audit': 'admin',
    '/admin/security-audit/summary': 'admin',
    '/admin/users': 'admin',
}

class ServiceClient:
    def __init__(self, service_urls: Dict[str, str]):
        self.service_urls = service_urls
        self.client = httpx.AsyncClient(timeout=30.0)

    async def forward_request(self, service: str, path: str, method: str,
                            headers: Dict[str, str], data: Optional[Any] = None,
                            params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Forward request to appropriate microservice."""
        service_url = self.service_urls.get(service)
        if not service_url:
            raise HTTPException(status_code=503, detail=f"Service {service} not available")

        url = f"{service_url}{path}"

        # Prepare headers (remove host header)
        forward_headers = {k: v for k, v in headers.items() if k.lower() not in ['host', 'content-length']}

        try:
            if method.upper() == 'GET':
                response = await self.client.get(url, headers=forward_headers, params=params)
            elif method.upper() == 'POST':
                response = await self.client.post(url, headers=forward_headers, json=data, params=params)
            elif method.upper() == 'PUT':
                response = await self.client.put(url, headers=forward_headers, json=data, params=params)
            elif method.upper() == 'DELETE':
                response = await self.client.delete(url, headers=forward_headers, params=params)
            else:
                raise HTTPException(status_code=405, detail=f"Method {method} not allowed")

            if response.status_code >= 400:
                # Try to parse error response
                try:
                    error_data = response.json()
                    raise HTTPException(status_code=response.status_code, detail=error_data.get('detail', 'Service error'))
                except:
                    raise HTTPException(status_code=response.status_code, detail=response.text)

            return response.json()

        except httpx.RequestError as e:
            logger.error(f"Request to {service} failed: {e}")
            raise HTTPException(status_code=503, detail=f"Service {service} unavailable")

    async def close(self):
        await self.client.aclose()

# Global service client
service_client = ServiceClient(SERVICE_URLS)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("API Gateway startup")
    yield
    logger.info("API Gateway shutdown")
    await service_client.close()

app = FastAPI(
    title="AstraRAG API Gateway",
    description="Microservices API Gateway for AstraRAG",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware (simplified for gateway)
@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    # Basic rate limiting - in production, use Redis
    response = await call_next(request)
    return response

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"Gateway Request: {request.method} {request.url}")

    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"Gateway Response: {request.method} {request.url} - Status: {response.status_code} - Time: {process_time:.3f}s")
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"Gateway Request failed: {request.method} {request.url} - Error: {str(e)} - Time: {process_time:.3f}s")
        raise

def get_service_for_path(path: str) -> Optional[str]:
    """Determine which service handles the given path."""
    # Check exact matches first
    if path in ROUTE_MAPPINGS:
        return ROUTE_MAPPINGS[path]

    # Check prefix matches
    for route_prefix, service in ROUTE_MAPPINGS.items():
        if path.startswith(route_prefix):
            return service

    return None

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def gateway_handler(
    request: Request,
    path: str,
    user: Optional[dict] = Depends(require_auth)
):
    """Main gateway handler that routes requests to appropriate services."""

    # Health check bypasses authentication
    if path == "health":
        return await health_check()

    # Determine target service
    service = get_service_for_path(f"/{path}")
    if not service:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    # Get request data
    try:
        body = await request.json() if request.method in ["POST", "PUT", "PATCH"] else None
    except:
        body = None

    # Get query parameters
    query_params = dict(request.query_params)

    # Forward request to service
    try:
        response_data = await service_client.forward_request(
            service=service,
            path=f"/{path}",
            method=request.method,
            headers=dict(request.headers),
            data=body,
            params=query_params
        )
        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Gateway error for {path}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    """Gateway health check."""
    health_status = {
        "status": "healthy",
        "service": "api-gateway",
        "timestamp": datetime.now().isoformat()
    }

    # Check service connectivity
    service_health = {}
    for service_name, service_url in SERVICE_URLS.items():
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{service_url}/health")
                service_health[service_name] = "healthy" if response.status_code == 200 else "unhealthy"
        except:
            service_health[service_name] = "unreachable"

    health_status["services"] = service_health

    # Determine overall health
    if any(status != "healthy" for status in service_health.values()):
        health_status["status"] = "degraded"

    return health_status

@app.get("/services")
async def list_services(user: dict = Depends(require_role(['superadmin']))):
    """List all registered services (admin only)."""
    return {
        "services": SERVICE_URLS,
        "route_mappings": ROUTE_MAPPINGS
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)