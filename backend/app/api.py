import sys
import os
import logging
import time
import json
import uuid
import io
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, List
import jwt
import psycopg2

from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Depends  # pyright: ignore[reportMissingImports]
from fastapi.responses import JSONResponse  # pyright: ignore[reportMissingImports]
from fastapi.middleware.cors import CORSMiddleware  # pyright: ignore[reportMissingImports]
from pydantic import BaseModel  # pyright: ignore[reportMissingImports]
from upstash_redis import Redis   # pyright: ignore[reportMissingImports]

from backend.core.auth import authenticate_user, generate_tokens, store_refresh_token, initialize_auth_db, require_auth, require_role, create_invite, register_user, setup_mfa, verify_mfa, enable_mfa
from backend.core.audit import log_audit_event
from backend.core.rag_pipeline import load_and_chunk_docs, create_vector_store
from backend.services.search import search_service
from backend.services.analytics import analytics_service
from backend.core.collaboration import collaboration_service, handle_collaboration_event
from backend.core.security_audit import security_audit_service
from config.config import UPLOADED_DOCS_DIR, POSTGRES_URL, REDIS_URL, REDIS_TOKEN, JWT_SECRET, GOOGLE_API_KEY, ELASTICSEARCH_URL

# Add project root to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('backend.log', mode='a')
    ]
)

JWT_ALGORITHM = "HS256"  # Should match auth.py

# Try to import document processing libraries
try:
    from unstructured.partition.pdf import partition_pdf
    UNSTRUCTURED_AVAILABLE = True
except ImportError:
    UNSTRUCTURED_AVAILABLE = False

try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False

try:
    BOTO3_AVAILABLE = False  # boto3 removed as unused
except ImportError:
    BOTO3_AVAILABLE = False

logger = logging.getLogger(__name__)

def validate_environment():
    """Validate required environment variables on startup."""
    required_vars = {
        'JWT_SECRET': JWT_SECRET,
        'POSTGRES_URL': POSTGRES_URL,
        'REDIS_URL': REDIS_URL,
        'REDIS_TOKEN': REDIS_TOKEN,
        'GOOGLE_API_KEY': GOOGLE_API_KEY,
    }

    missing_vars = []
    for var_name, var_value in required_vars.items():
        if not var_value:
            missing_vars.append(var_name)

    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    logger.info("Environment validation passed")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    validate_environment()
    initialize_auth_db()
    logger.info("Application startup completed")
    yield
    # Shutdown
    logger.info("Application shutdown")

app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Frontend dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"

    # Define rate limits by endpoint
    rate_limits = {
        "/auth/login": 5,  # 5 login attempts per minute
        "/auth/register": 3,  # 3 registrations per minute
        "/policies/upload": 10,  # 10 uploads per minute
        "/qa/ask": 20,  # 20 QA queries per minute
    }

    # Check if endpoint has rate limiting
    path = str(request.url.path)
    limit = None
    for endpoint, lim in rate_limits.items():
        if path.startswith(endpoint):
            limit = lim
            break

    if limit:
        try:
            redis = Redis(url=REDIS_URL or "", token=REDIS_TOKEN or "")
            key = f"ratelimit:{client_ip}:{path}"
            current_time = int(time.time())
            window_start = current_time - 60  # 1 minute window

            # Use sorted set to track timestamps
            redis.zadd(key, {str(current_time): current_time})
            redis.zremrangebyscore(key, 0, window_start)
            count = redis.zcard(key)

            # Set expiration
            redis.expire(key, 120)

            if count >= limit:
                logger.warning(f"Rate limit exceeded for {client_ip} on {path}")
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Try again later."}
                )
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Continue without rate limiting if Redis fails

    response = await call_next(request)
    return response

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"Request: {request.method} {request.url}")

    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"Response: {request.method} {request.url} - Status: {response.status_code} - Time: {process_time:.3f}s")
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"Request failed: {request.method} {request.url} - Error: {str(e)} - Time: {process_time:.3f}s")
        raise

class QueryRequest(BaseModel):
    query: str
    token: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    user_id: str
    username: str
    role: str
    organization_id: int

class TokensResponse(BaseModel):
    access_token: str
    refresh_token: str

class LoginResponse(BaseModel):
    user: UserResponse
    tokens: TokensResponse

class HealthResponse(BaseModel):
    status: str
    database: str
    redis: str
    timestamp: str

class InviteRequest(BaseModel):
    email: str
    role: str

class RegisterRequest(BaseModel):
    invite_token: str
    email: str
    password: str

class ApproveDocumentRequest(BaseModel):
    doc_id: str
    action: str  # 'approve' or 'reject'

class MFASetupRequest(BaseModel):
    code: str

class MFAVerifyRequest(BaseModel):
    code: str

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

@app.post("/search/documents", response_model=SearchResponse)
async def search_documents(request: SearchRequest, user: dict = Depends(require_auth)):
    """Advanced search with faceted filtering."""
    try:
        result, total = search_service.search_documents(
            query=request.query,
            filters=request.filters or {},
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
async def get_search_facets(user: dict = Depends(require_auth)):
    """Get available search facets."""
    try:
        # Get all documents for facet calculation
        result, _ = search_service.search_documents(query="", filters={}, page=1, size=10000)
        return result.get("facets", {}) if result else {}
    except Exception as e:
        logger.error(f"Facets error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get facets")

@app.get("/analytics/user-activity")
async def get_user_activity_analytics(days: int = 30, user: dict = Depends(require_role(['admin', 'superadmin']))):
    """Get user activity analytics (admin only)."""
    try:
        return analytics_service.get_user_activity_metrics(days)
    except Exception as e:
        logger.error(f"User activity analytics error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user activity analytics")

@app.get("/analytics/system-metrics")
async def get_system_metrics(hours: int = 24, user: dict = Depends(require_role(['admin', 'superadmin']))):
    """Get system performance metrics (admin only)."""
    try:
        return analytics_service.get_system_metrics(hours)
    except Exception as e:
        logger.error(f"System metrics error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system metrics")

@app.post("/analytics/track")
async def track_analytics_event(
    event_type: str,
    event_data: Optional[Dict[str, Any]] = None,
    user: dict = Depends(require_auth),
    request: Optional[Request] = None
):
    """Track user analytics events."""
    try:
        session_id = request.cookies.get('session_id') if request else None
        ip_address = request.client.host if request and request.client else None
        user_agent = request.headers.get('user-agent') if request else None

        analytics_service.track_event(
            user_id=user['user_id'],
            event_type=event_type,
            event_data=event_data or {},
            session_id=session_id or "",
            ip_address=ip_address or "",
            user_agent=user_agent or ""
        )
        return {"message": "Event tracked successfully"}
    except Exception as e:
        logger.error(f"Analytics tracking error: {e}")
        raise HTTPException(status_code=500, detail="Failed to track event")

# Collaboration endpoints
@app.get("/documents/{doc_id}/collaboration/status")
async def get_document_collaboration_status(doc_id: str, user: dict = Depends(require_auth)):
    """Get collaboration status for a document."""
    try:
        status = collaboration_service.get_document_collaboration_status(doc_id)
        return status
    except Exception as e:
        logger.error(f"Failed to get collaboration status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get collaboration status")

@app.get("/documents/{doc_id}/comments")
async def get_document_comments(doc_id: str, user: dict = Depends(require_auth)):
    """Get all comments for a document."""
    try:
        comments = collaboration_service.get_document_comments(doc_id)
        return comments
    except Exception as e:
        logger.error(f"Failed to get document comments: {e}")
        raise HTTPException(status_code=500, detail="Failed to get comments")

@app.post("/documents/{doc_id}/comments")
async def add_document_comment(
    doc_id: str,
    content: str,
    parent_comment_id: Optional[str] = None,
    position_data: Optional[Dict[str, Any]] = None,
    comment_type: str = "text",
    user: dict = Depends(require_auth)
):
    """Add a comment to a document."""
    try:
        comment_id = collaboration_service.add_document_comment(
            doc_id=doc_id,
            content=content,
            author_id=user['user_id'],
            parent_comment_id=parent_comment_id or "",
            position_data=position_data or {},
            comment_type=comment_type
        )

        if comment_id:
            return {"message": "Comment added successfully", "comment_id": comment_id}
        else:
            raise HTTPException(status_code=500, detail="Failed to add comment")
    except Exception as e:
        logger.error(f"Failed to add comment: {e}")
        raise HTTPException(status_code=500, detail="Failed to add comment")

@app.put("/documents/comments/{comment_id}/status")
async def update_comment_status(
    comment_id: str,
    is_resolved: bool,
    user: dict = Depends(require_auth)
):
    """Update comment resolution status."""
    try:
        success = collaboration_service.update_comment_status(comment_id, is_resolved, user['user_id'])
        if success:
            return {"message": "Comment status updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Comment not found")
    except Exception as e:
        logger.error(f"Failed to update comment status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update comment status")

@app.get("/documents/{doc_id}/versions")
async def get_document_versions(doc_id: str, user: dict = Depends(require_auth)):
    """Get all versions of a document."""
    try:
        versions = collaboration_service.get_document_versions(doc_id)
        return versions
    except Exception as e:
        logger.error(f"Failed to get document versions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get versions")

@app.post("/documents/{doc_id}/versions")
async def create_document_version(
    doc_id: str,
    version_number: int,
    content_hash: str,
    changes_summary: Optional[str] = None,
    user: dict = Depends(require_auth)
):
    """Create a new document version."""
    try:
        success = collaboration_service.create_document_version(
            doc_id=doc_id,
            version_number=version_number,
            content_hash=content_hash,
            changes_summary=changes_summary or "",
            created_by=user['user_id']
        )

        if success:
            return {"message": "Version created successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create version")
    except Exception as e:
        logger.error(f"Failed to create document version: {e}")
        raise HTTPException(status_code=500, detail="Failed to create version")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint that verifies database and Redis connectivity."""
    health_status = {
        "status": "healthy",
        "database": "ok",
        "redis": "ok",
        "timestamp": datetime.utcnow().isoformat()
    }

    # Check database connectivity
    try:
        conn = psycopg2.connect(POSTGRES_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        conn.close()
        logger.info("Database health check passed")
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
        logger.error(f"Database health check failed: {e}")

    # Check Redis connectivity
    try:
        redis = Redis(url=REDIS_URL or "", token=REDIS_TOKEN or "")
        redis.ping()
        logger.info("Redis health check passed")
    except Exception as e:
        health_status["redis"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
        logger.error(f"Redis health check failed: {e}")

    return HealthResponse(**health_status)

@app.post("/qa/ask")
async def query_rag(request: QueryRequest, user: dict = Depends(require_auth)):
    try:
        # Check cache first
        cache_key = f"qa:{user['user_id']}:{hash(request.query) % 1000000}"
        try:
            redis = Redis(url=REDIS_URL or "", token=REDIS_TOKEN or "")
            cached_result = redis.get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for user {user['user_id']}")
                return json.loads(cached_result)
        except Exception as e:
            logger.warning(f"Cache read error: {e}")

        # Try to use RAG pipeline if available
        try:
            # Load and process documents
            chunks = await load_and_chunk_docs(UPLOADED_DOCS_DIR)
            if chunks:
                vector_store = await create_vector_store(chunks)
                if vector_store:
                    # For now, use simple retriever without LLM dependencies
                    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
                    docs = retriever.get_relevant_documents(request.query)

                    # Simple answer generation (placeholder for LLM)
                    context = "\n".join([doc.page_content[:500] for doc in docs[:3]])
                    answer = f"Based on the company documents: {context[:200]}..."

                    result = {
                        "answer": answer,
                        "sources": [{"doc_id": "placeholder", "chunk_index": i} for i in range(len(docs))]
                    }
                else:
                    result = {"answer": "Vector store not available. Please check system configuration.", "sources": []}
            else:
                result = {"answer": "No documents available for querying.", "sources": []}
        except Exception as e:
            logger.warning(f"RAG pipeline error: {e}")
            result = {"answer": "RAG system temporarily unavailable. Please try again later.", "sources": []}

        # Store QA session in database
        try:
            conn = psycopg2.connect(POSTGRES_URL)
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO qa_sessions (user_id, question, answer, used_chunks)
            VALUES (%s, %s, %s, %s)
            """, (user["user_id"], request.query, result["answer"], result["sources"]))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Failed to store QA session: {e}")

        # Cache the result
        try:
            redis = Redis(url=REDIS_URL or "", token=REDIS_TOKEN or "")
            redis.setex(cache_key, 3600, json.dumps(result))  # Cache for 1 hour
        except Exception as e:
            logger.warning(f"Cache write error: {e}")

        return result
    except Exception as e:
        logger.error(f"QA query error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

class LoginResponseWithMFA(BaseModel):
    user: UserResponse
    tokens: Optional[TokensResponse] = None
    mfa_required: bool = False
    temp_token: Optional[str] = None

@app.post("/auth/login", response_model=LoginResponseWithMFA)
async def login(request: LoginRequest):
    logger.info(f"Login attempt for user: {request.email}")
    try:
        user_data = authenticate_user(request.email, request.password)
        if not user_data:
            logger.warning(f"Failed login attempt for user: {request.email} - Invalid credentials")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Check if MFA is required for admin roles
        mfa_required = user_data["role"].startswith("admin") or user_data["role"] == "superadmin"

        if mfa_required and user_data.get("mfa_enabled", False):
            # Generate temporary token for MFA verification
            temp_payload = {
                "email": user_data["email"],
                "user_id": user_data["user_id"],
                "mfa_pending": True,
                "exp": datetime.utcnow() + timedelta(minutes=5)  # 5 minutes for MFA
            }
            temp_token = jwt.encode(temp_payload, JWT_SECRET or "", algorithm=JWT_ALGORITHM)

            logger.info(f"MFA required for user: {request.email}")
            return LoginResponseWithMFA(
                user=UserResponse(
                    user_id=user_data["user_id"],
                    username=user_data["email"],
                    role=user_data["role"],
                    organization_id=1
                ),
                mfa_required=True,
                temp_token=temp_token
            )

        # No MFA required or not enabled
        access_token, refresh_token = generate_tokens(user_data)
        store_refresh_token(request.email, refresh_token)

        # Update last_login
        conn = psycopg2.connect(POSTGRES_URL)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET last_login = NOW() WHERE id = %s", (user_data["user_id"],))
        conn.commit()
        conn.close()

        logger.info(f"Successful login for user: {request.email}")
        return LoginResponseWithMFA(
            user=UserResponse(
                user_id=user_data["user_id"],
                username=user_data["email"],
                role=user_data["role"],
                organization_id=1
            ),
            tokens=TokensResponse(
                access_token=access_token,
                refresh_token=refresh_token
            ),
            mfa_required=False
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login for user {request.email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/admin/invite")
async def create_user_invite(request: InviteRequest, user: dict = Depends(require_role(['superadmin'])), req: Optional[Request] = None):
    """Create an invite for a new user. Requires superadmin role."""
    try:
        client_ip = req.client.host if req and req.client else None
        raw_token = create_invite(request.email, request.role, user["user_id"], client_ip)
        # In a real implementation, send email with token
        logger.info(f"Invite created for {request.email} with role {request.role}")
        return {"message": "Invite created", "email": request.email, "token": raw_token}  # Return token for demo
    except Exception as e:
        logger.error(f"Error creating invite: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/register")
async def register_new_user(request: RegisterRequest, req: Optional[Request] = None):
    """Register a new user using an invite token."""
    try:
        client_ip = req.client.host if req and req.client else None
        user_data = register_user(request.email, request.password, request.invite_token, client_ip)
        logger.info(f"User registered: {request.email}")
        return {"message": "User registered successfully", "user": user_data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/admin/invites")
async def list_invites(user: dict = Depends(require_role(['superadmin']))):
    """List all invites (superadmin only)."""
    try:
        conn = psycopg2.connect(POSTGRES_URL)
        cursor = conn.cursor()
        cursor.execute("""
        SELECT id, email, role, created_by, expires_at, used, used_by, created_at
        FROM invites
        ORDER BY created_at DESC
        """)
        invites = cursor.fetchall()
        conn.close()

        result = []
        for invite in invites:
            result.append({
                "id": str(invite[0]),
                "email": invite[1],
                "role": invite[2],
                "created_by": str(invite[3]),
                "expires_at": invite[4].isoformat() if invite[4] else None,
                "used": invite[5],
                "used_by": str(invite[6]) if invite[6] else None,
                "created_at": invite[7].isoformat() if invite[7] else None
            })

        return result
    except Exception as e:
        logger.error(f"Error listing invites: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/admin/revoke-invite/{invite_id}")
async def revoke_invite(invite_id: str, user: dict = Depends(require_role(['superadmin'])), req: Optional[Request] = None):
    """Revoke an invite by setting expires_at to now (superadmin only)."""
    try:
        client_ip = req.client.host if req and req.client else None
        conn = psycopg2.connect(POSTGRES_URL)
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE invites SET expires_at = NOW() WHERE id = %s AND used = FALSE
        """, (invite_id,))
        affected_rows = cursor.rowcount
        conn.commit()
        conn.close()

        if affected_rows == 0:
            raise HTTPException(status_code=404, detail="Invite not found or already used")

        # Audit log
        log_audit_event(
            actor_id=user["user_id"],
            action="invite_revoked",
            target=invite_id,
            meta={"reason": "revoked_by_admin"},
            ip=client_ip
        )

        return {"message": "Invite revoked successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking invite: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/policies/upload")
async def upload_policies(
    file: UploadFile = File(...),
    user: dict = Depends(require_role(['admin:hr'])),
    req: Optional[Request] = None
):
    try:
        client_ip = req.client.host if req and req.client else None

        # Validate file type
        if not file.filename or not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        # Validate file size (<10MB)
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Seek back to beginning
        if file_size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size must be less than 10MB")

        # Read file content
        file_content = await file.read()

        # TODO: Run ClamAV scan for malware
        # For now, skip malware scanning

        # Generate S3 path
        doc_id = str(uuid.uuid4())
        s3_path = f"policies/{doc_id}_{file.filename}"

        # Upload to S3 if available
        if BOTO3_AVAILABLE:
            try:
                # TODO: Configure S3 client with proper credentials
                # s3_client = boto3.client('s3')
                # s3_client.upload_fileobj(file.file, bucket_name, s3_path)
                pass
            except Exception as e:
                logger.warning(f"S3 upload failed: {e}")

        # Parse document with unstructured
        extracted_text = ""
        metadata = {}

        if UNSTRUCTURED_AVAILABLE:
            try:
                # Reset file pointer
                file.file.seek(0)
                pdf_stream = io.BytesIO(file_content)

                from unstructured.partition.pdf import partition_pdf
                elements = partition_pdf(file=pdf_stream, strategy="hi_res")
                extracted_text = "\n".join([str(element) for element in elements])

                # Extract metadata
                metadata = {
                    "filename": file.filename,
                    "file_size": file_size,
                    "pages": len([e for e in elements if hasattr(e, 'metadata') and e.metadata.get('page_number')]),
                    "extracted_at": datetime.utcnow().isoformat()
                }
                if metadata.get("pages") is None:
                    metadata["pages"] = 0
            except Exception as e:
                logger.warning(f"Document parsing failed: {e}")
                extracted_text = "Document parsing failed"
        else:
            logger.warning("Unstructured not available, skipping document parsing")

        # PII Anonymization
        if PRESIDIO_AVAILABLE:
            try:
                from presidio_analyzer import AnalyzerEngine
                from presidio_anonymizer import AnonymizerEngine
                analyzer = AnalyzerEngine()
                anonymizer = AnonymizerEngine()

                results = analyzer.analyze(text=extracted_text, language='en')
                # Anonymize text (not stored, only metadata updated)
                from typing import cast, Sequence
                anonymizer.anonymize(text=extracted_text, analyzer_results=cast(Sequence, results))

                metadata["pii_detected"] = len(results) > 0
                metadata["pii_count"] = len(results)
            except Exception as e:
                logger.warning(f"PII anonymization failed: {e}")
        else:
            logger.warning("Presidio not available, skipping PII anonymization")

        # Store document in database
        conn = psycopg2.connect(POSTGRES_URL)
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO documents (id, original_filename, s3_path, uploaded_by, status, metadata)
        VALUES (%s, %s, %s, %s, %s, %s)
        """, (doc_id, file.filename, s3_path, user["user_id"], "pending_review", metadata))
        conn.commit()
        conn.close()

        # TODO: Implement chunking and embeddings
        # TODO: Store chunks in Milvus

        # Index document in Elasticsearch
        try:
            file_type = file.filename.split('.')[-1].lower() if file.filename and '.' in file.filename else 'unknown'
            search_service.index_document(
                doc_id=doc_id,
                filename=file.filename or "unknown",
                content=extracted_text,
                uploaded_by=user["user_id"],
                uploaded_at=datetime.utcnow().isoformat(),
                file_type=file_type,
                file_size=file_size,
                status="pending_review",
                metadata=metadata
            )
            logger.info(f"Document {doc_id} indexed in Elasticsearch")
        except Exception as e:
            logger.warning(f"Failed to index document {doc_id} in Elasticsearch: {e}")

        # Audit log
        log_audit_event(
            actor_id=user["user_id"],
            action="document_uploaded",
            target=doc_id,
            meta={"filename": file.filename, "s3_path": s3_path, "status": "pending_review"},
            ip=client_ip
        )

        return {
            "message": "Document uploaded successfully and queued for processing",
            "doc_id": doc_id,
            "filename": file.filename,
            "status": "pending_review"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/admin/documents/pending")
async def get_pending_documents(user: dict = Depends(require_role(['superadmin']))):
    """Get list of documents pending approval."""
    try:
        conn = psycopg2.connect(POSTGRES_URL)
        cursor = conn.cursor()
        cursor.execute("""
        SELECT id, original_filename, uploaded_by, uploaded_at, metadata
        FROM documents
        WHERE status = 'pending_review'
        ORDER BY uploaded_at DESC
        """)
        documents = cursor.fetchall()
        conn.close()

        return [
            {
                "doc_id": str(row[0]),
                "filename": row[1],
                "uploaded_by": str(row[2]),
                "uploaded_at": row[3].isoformat() if row[3] else None,
                "metadata": row[4] or {}
            } for row in documents
        ]
    except Exception as e:
        logger.error(f"Error getting pending documents: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/admin/documents/approve")
async def approve_document(request: ApproveDocumentRequest, user: dict = Depends(require_role(['superadmin'])), req: Optional[Request] = None):
    """Approve or reject a document."""
    try:
        new_status = "active" if request.action == "approve" else "rejected"

        conn = psycopg2.connect(POSTGRES_URL)
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE documents SET status = %s WHERE id = %s AND status = 'pending_review'
        RETURNING id, original_filename
        """, (new_status, request.doc_id))
        result = cursor.fetchone()
        conn.commit()
        conn.close()

        if not result:
            raise HTTPException(status_code=404, detail="Document not found or already processed")

        # Update document status in Elasticsearch
        try:
            search_service.update_document(request.doc_id, {"status": new_status})
            logger.info(f"Updated document {request.doc_id} status in Elasticsearch to {new_status}")
        except Exception as e:
            logger.warning(f"Failed to update document {request.doc_id} in Elasticsearch: {e}")

        # Audit log
        log_audit_event(
            actor_id=user["user_id"],
            action=f"document_{request.action}d",
            target=request.doc_id,
            meta={"filename": result[1], "new_status": new_status},
            ip=req.client.host if req and req.client else None
        )

        return {"message": f"Document {request.action}d successfully", "doc_id": request.doc_id, "status": new_status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/auth/mfa/setup")
async def setup_user_mfa(user: dict = Depends(require_auth)):
    """Setup MFA for the authenticated user (admin roles required)."""
    try:
        # Check if user has admin role
        if not user["role"].startswith("admin") and user["role"] != "superadmin":
            raise HTTPException(status_code=403, detail="MFA setup requires admin privileges")

        mfa_data = setup_mfa(user["user_id"])
        return {
            "message": "MFA setup initiated",
            "provisioning_uri": mfa_data["provisioning_uri"],
            "backup_codes": mfa_data["backup_codes"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting up MFA: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/auth/mfa/verify")
async def verify_user_mfa(request: MFASetupRequest, user: dict = Depends(require_auth)):
    """Verify MFA setup code and enable MFA."""
    try:
        if verify_mfa(user["user_id"], request.code):
            enable_mfa(user["user_id"])
            return {"message": "MFA enabled successfully"}
        else:
            raise HTTPException(status_code=400, detail="Invalid MFA code")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying MFA: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/auth/mfa/authenticate")
async def authenticate_mfa(request: MFAVerifyRequest, user: dict = Depends(require_auth)):
    """Verify MFA code during login for MFA-enabled users."""
    try:
        if verify_mfa(user["user_id"], request.code):
            return {"message": "MFA authentication successful"}
        else:
            raise HTTPException(status_code=400, detail="Invalid MFA code")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error authenticating MFA: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/auth/mfa/complete-login")
async def complete_mfa_login(request: MFAVerifyRequest):
    """Complete login after MFA verification using temp token."""
    try:
        # This would need a custom dependency to validate temp MFA token
        # For now, return placeholder
        return {"message": "MFA login completion - needs implementation"}
    except Exception as e:
        logger.error(f"Error completing MFA login: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/auth/validate")
async def validate_token_endpoint(user: dict = Depends(require_auth)):
    """Validate the current access token and return user info."""
    try:
        return {
            "valid": True,
            "user": {
                "user_id": user["user_id"],
                "email": user["email"],
                "role": user["role"],
                "is_active": user["is_active"]
            }
        }
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

# Security audit endpoints
@app.get("/admin/security-audit")
async def run_security_audit(user: dict = Depends(require_role(['superadmin']))):
    """Run comprehensive security audit (superadmin only)."""
    try:
        audit_results = security_audit_service.run_comprehensive_security_audit()
        return audit_results
    except Exception as e:
        logger.error(f"Security audit failed: {e}")
        raise HTTPException(status_code=500, detail="Security audit failed")

@app.get("/admin/security-audit/summary")
async def get_security_audit_summary(user: dict = Depends(require_role(['admin', 'superadmin']))):
    """Get security audit summary (admin+ only)."""
    try:
        audit_results = security_audit_service.run_comprehensive_security_audit()
        # Return only summary for regular admins
        return {
            "timestamp": audit_results["timestamp"],
            "overall_score": audit_results["overall_score"],
            "critical_issues_count": len(audit_results["critical_issues"]),
            "high_issues_count": len(audit_results["high_issues"]),
            "medium_issues_count": len(audit_results["medium_issues"]),
            "low_issues_count": len(audit_results["low_issues"]),
            "passed_checks_count": len(audit_results["passed_checks"])
        }
    except Exception as e:
        logger.error(f"Security audit summary failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get security audit summary")

@app.get("/admin/users")
async def get_users(user: dict = Depends(require_role(['superadmin']))):
    try:
        conn = psycopg2.connect(POSTGRES_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, role, is_active FROM users")
        users = cursor.fetchall()
        conn.close()

        return [
            {
                "user_id": str(row[0]),
                "email": row[1],
                "role": row[2],
                "is_active": row[3]
            } for row in users
        ]
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
