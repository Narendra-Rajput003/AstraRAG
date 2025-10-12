import sys
import os
import logging
import uuid
import io
from datetime import datetime
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import psycopg2
import boto3
from botocore.exceptions import NoCredentialsError

# Add project root to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.config import (
    POSTGRES_URL, UPLOADED_DOCS_DIR, MINIO_ENDPOINT,
    MINIO_ACCESS_KEY, MINIO_SECRET_KEY
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

class ApproveDocumentRequest(BaseModel):
    doc_id: str
    action: str  # 'approve' or 'reject'

def get_db_connection():
    return psycopg2.connect(POSTGRES_URL)

def get_minio_client():
    """Get MinIO/S3 client for document storage."""
    return boto3.client(
        's3',
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        region_name='us-east-1'  # MinIO doesn't require a specific region
    )

def upload_to_minio(file_content: bytes, filename: str, doc_id: str) -> str:
    """Upload file to MinIO/S3 storage."""
    try:
        s3_client = get_minio_client()
        bucket_name = 'astrarag-documents'
        s3_path = f"documents/{doc_id}/{filename}"

        # Create bucket if it doesn't exist
        try:
            s3_client.head_bucket(Bucket=bucket_name)
        except:
            s3_client.create_bucket(Bucket=bucket_name)

        # Upload file
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_path,
            Body=file_content,
            ContentType='application/pdf'
        )

        return s3_path

    except NoCredentialsError:
        logger.warning("MinIO credentials not configured, using local storage")
        return save_locally(file_content, filename, doc_id)
    except Exception as e:
        logger.error(f"MinIO upload failed: {e}")
        return save_locally(file_content, filename, doc_id)

def save_locally(file_content: bytes, filename: str, doc_id: str) -> str:
    """Fallback: save file locally."""
    local_path = os.path.join(UPLOADED_DOCS_DIR, f"{doc_id}_{filename}")
    os.makedirs(os.path.dirname(local_path), exist_ok=True)

    with open(local_path, 'wb') as f:
        f.write(file_content)

    return local_path

def extract_text_from_pdf(file_content: bytes) -> tuple[str, Dict[str, Any]]:
    """Extract text and metadata from PDF."""
    extracted_text = ""
    metadata = {}

    if UNSTRUCTURED_AVAILABLE:
        try:
            pdf_stream = io.BytesIO(file_content)
            elements = partition_pdf(file=pdf_stream, strategy="hi_res")

            extracted_text = "\n".join([str(element) for element in elements])

            # Extract metadata
            metadata = {
                "filename": "uploaded_file.pdf",  # Will be overridden
                "pages": len([e for e in elements if hasattr(e, 'metadata') and e.metadata.get('page_number')]),
                "extracted_at": datetime.now().isoformat(),
                "text_length": len(extracted_text)
            }

        except Exception as e:
            logger.warning(f"Document parsing failed: {e}")
            extracted_text = "Document parsing failed"
    else:
        logger.warning("Unstructured not available, skipping document parsing")

    return extracted_text, metadata

def anonymize_text(text: str) -> tuple[str, Dict[str, Any]]:
    """Anonymize sensitive information in text."""
    pii_metadata = {}

    if PRESIDIO_AVAILABLE:
        try:
            analyzer = AnalyzerEngine()
            anonymizer = AnonymizerEngine()

            results = analyzer.analyze(text=text, language='en')
            # Note: In production, you might want to anonymize the text
            # For now, we just detect PII for metadata

            pii_metadata = {
                "pii_detected": len(results) > 0,
                "pii_count": len(results),
                "pii_types": list(set([result.entity_type for result in results]))
            }

        except Exception as e:
            logger.warning(f"PII anonymization failed: {e}")
    else:
        logger.warning("Presidio not available, skipping PII anonymization")

    return text, pii_metadata

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Document service startup")
    yield
    logger.info("Document service shutdown")

app = FastAPI(
    title="Document Service",
    description="Document management and processing microservice",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "document-service",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/policies/upload")
async def upload_document(
    file: UploadFile = File(...),
    req: Request = None
):
    """Upload and process a document."""
    user_id = req.headers.get("X-User-ID") if req else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Validate file size (<10MB)
    file_content = await file.read()
    file_size = len(file_content)
    if file_size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be less than 10MB")

    # Reset file pointer for processing
    await file.seek(0)

    try:
        # Generate document ID
        doc_id = str(uuid.uuid4())

        # Upload to storage
        s3_path = upload_to_minio(file_content, file.filename, doc_id)

        # Extract text and metadata
        extracted_text, pdf_metadata = extract_text_from_pdf(file_content)
        pdf_metadata["filename"] = file.filename
        pdf_metadata["file_size"] = file_size

        # Anonymize text and get PII metadata
        processed_text, pii_metadata = anonymize_text(extracted_text)

        # Combine metadata
        metadata = {**pdf_metadata, **pii_metadata}

        # Store document in database
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO documents (
            id, original_filename, s3_path, uploaded_by,
            status, metadata, file_type, file_size, content_hash
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            doc_id,
            file.filename,
            s3_path,
            user_id,
            "pending_review",
            metadata,
            "pdf",
            file_size,
            hash(processed_text)  # Simple content hash
        ))

        conn.commit()
        conn.close()

        logger.info(f"Document {doc_id} uploaded and processed successfully")

        return {
            "message": "Document uploaded successfully and queued for processing",
            "doc_id": doc_id,
            "filename": file.filename,
            "status": "pending_review",
            "metadata": metadata
        }

    except Exception as e:
        logger.error(f"Document upload error: {e}")
        raise HTTPException(status_code=500, detail="Document upload failed")

@app.get("/admin/documents/pending")
async def get_pending_documents():
    """Get list of documents pending approval."""
    try:
        conn = get_db_connection()
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
async def approve_document(request: ApproveDocumentRequest, req: Request = None):
    """Approve or reject a document."""
    user_id = req.headers.get("X-User-ID") if req else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    try:
        new_status = "active" if request.action == "approve" else "rejected"

        conn = get_db_connection()
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

        logger.info(f"Document {request.doc_id} {request.action}d by user {user_id}")

        return {
            "message": f"Document {request.action}d successfully",
            "doc_id": request.doc_id,
            "status": new_status
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving document: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/documents/{doc_id}")
async def get_document(doc_id: str, req: Request = None):
    """Get document details."""
    user_id = req.headers.get("X-User-ID") if req else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT id, original_filename, s3_path, uploaded_by, uploaded_at,
               status, metadata, file_type, file_size
        FROM documents WHERE id = %s
        """, (doc_id,))

        doc = cursor.fetchone()
        conn.close()

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        return {
            "doc_id": str(doc[0]),
            "filename": doc[1],
            "s3_path": doc[2],
            "uploaded_by": str(doc[3]),
            "uploaded_at": doc[4].isoformat() if doc[4] else None,
            "status": doc[5],
            "metadata": doc[6] or {},
            "file_type": doc[7],
            "file_size": doc[8]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/documents")
async def list_documents(
    status: Optional[str] = None,
    uploaded_by: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    req: Request = None
):
    """List documents with optional filtering."""
    user_id = req.headers.get("X-User-ID") if req else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Build query
        query = """
        SELECT id, original_filename, uploaded_by, uploaded_at, status, metadata, file_size
        FROM documents
        WHERE 1=1
        """
        params = []

        if status:
            query += " AND status = %s"
            params.append(status)

        if uploaded_by:
            query += " AND uploaded_by = %s"
            params.append(uploaded_by)

        query += " ORDER BY uploaded_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor.execute(query, params)
        documents = cursor.fetchall()

        # Get total count
        count_query = "SELECT COUNT(*) FROM documents WHERE 1=1"
        count_params = []
        if status:
            count_query += " AND status = %s"
            count_params.append(status)
        if uploaded_by:
            count_query += " AND uploaded_by = %s"
            count_params.append(uploaded_by)

        cursor.execute(count_query, count_params)
        total = cursor.fetchone()[0]

        conn.close()

        return {
            "documents": [
                {
                    "doc_id": str(row[0]),
                    "filename": row[1],
                    "uploaded_by": str(row[2]),
                    "uploaded_at": row[3].isoformat() if row[3] else None,
                    "status": row[4],
                    "metadata": row[5] or {},
                    "file_size": row[6]
                } for row in documents
            ],
            "total": total,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)