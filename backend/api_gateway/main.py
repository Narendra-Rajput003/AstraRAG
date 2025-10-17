import logging
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api_gateway.routes import auth, documents, search, admin, analytics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthResponse:
    def __init__(self, status: str, timestamp: str):
        self.status = status
        self.timestamp = timestamp

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("API Gateway startup")
    yield
    logger.info("API Gateway shutdown")

app = FastAPI(
    title="API Gateway",
    description="API Gateway for AstraRAG microservices",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Frontend dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(search.router)
app.include_router(admin.router)
app.include_router(analytics.router)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "api-gateway",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)