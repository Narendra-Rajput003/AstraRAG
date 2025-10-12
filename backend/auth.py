import logging
from datetime import datetime, timedelta
import sys
import os
from typing import Optional

# Added a comment to force module reload
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..')) # Add project root to sys.path

import jwt  # pyright: ignore[reportMissingImports]
import psycopg2  # pyright: ignore[reportMissingModuleSource]
from upstash_redis import Redis   # pyright: ignore[reportMissingImports]
import secrets
from fastapi import Depends, HTTPException, Request  # pyright: ignore[reportMissingImports]
from config.config import JWT_SECRET, POSTGRES_URL, RATE_LIMIT_PER_MIN, REDIS_URL, REDIS_TOKEN, JWT_EXP_MINUTES, REFRESH_EXP_DAYS
from backend.security import hash_password, check_password, validate_password_policy
from backend.audit import log_audit_event

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# MFA imports
try:
    import pyotp  # pyright: ignore[reportMissingImports]
    PYOTP_AVAILABLE = True
except ImportError:
    logger.warning("pyotp not available, MFA disabled")
    pyotp = None
    PYOTP_AVAILABLE = False

JWT_ALGORITHM = "HS256"


def initialize_auth_db():
    conn = psycopg2.connect(POSTGRES_URL)
    cursor = conn.cursor()

    # Enable UUID extension
    cursor.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")

    # Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        email VARCHAR UNIQUE NOT NULL,
        password_hash VARCHAR NOT NULL,
        role VARCHAR NOT NULL DEFAULT 'employee',
        department VARCHAR,
        is_active BOOLEAN DEFAULT TRUE,
        mfa_enabled BOOLEAN DEFAULT FALSE,
        mfa_secret VARCHAR,
        backup_codes TEXT[],  -- Array of backup codes
        created_at TIMESTAMP DEFAULT NOW(),
        last_login TIMESTAMP,
        refresh_token VARCHAR
    )
    """)

    # Create invites table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invites (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        email VARCHAR NOT NULL,
        token_hash VARCHAR NOT NULL,
        role VARCHAR NOT NULL,
        created_by UUID REFERENCES users(id),
        used BOOLEAN DEFAULT FALSE,
        used_by UUID REFERENCES users(id),
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT NOW()
    )
    """)

    # Create audit_logs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        actor_id UUID REFERENCES users(id),
        action VARCHAR NOT NULL,
        target VARCHAR,
        meta JSONB,
        ip INET,
        created_at TIMESTAMP DEFAULT NOW()
    )
    """)

    # Create documents table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        original_filename VARCHAR NOT NULL,
        s3_path VARCHAR NOT NULL,
        uploaded_by UUID REFERENCES users(id),
        uploaded_at TIMESTAMP DEFAULT NOW(),
        status VARCHAR DEFAULT 'active',
        metadata JSONB
    )
    """)

    # Create chunks table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chunks (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        doc_id UUID REFERENCES documents(id) ON DELETE CASCADE,
        chunk_index INTEGER NOT NULL,
        text TEXT NOT NULL,
        embed_id VARCHAR NOT NULL,
        token_count INTEGER NOT NULL
    )
    """)

    # Create qa_sessions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS qa_sessions (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id UUID REFERENCES users(id),
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        used_chunks JSONB NOT NULL,
        timestamp TIMESTAMP DEFAULT NOW()
    )
    """)

    # Create analytics_events table for user activity tracking
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS analytics_events (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id UUID REFERENCES users(id),
        event_type VARCHAR NOT NULL,
        event_data JSONB,
        session_id VARCHAR,
        ip_address INET,
        user_agent TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    )
    """)

    # Create document_versions table for version tracking
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS document_versions (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        doc_id UUID REFERENCES documents(id) ON DELETE CASCADE,
        version_number INTEGER NOT NULL,
        content_hash VARCHAR NOT NULL,
        changes_summary TEXT,
        created_by UUID REFERENCES users(id),
        created_at TIMESTAMP DEFAULT NOW()
    )
    """)

    # Create document_comments table for collaborative review
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS document_comments (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        doc_id UUID REFERENCES documents(id) ON DELETE CASCADE,
        parent_comment_id UUID REFERENCES document_comments(id) ON DELETE CASCADE,
        content TEXT NOT NULL,
        author_id UUID REFERENCES users(id),
        position_data JSONB,  -- For PDF/Word annotations
        comment_type VARCHAR DEFAULT 'text',  -- text, annotation, highlight
        is_resolved BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    )
    """)

    # Create user_sessions table for session tracking
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_sessions (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id UUID REFERENCES users(id),
        session_token VARCHAR UNIQUE NOT NULL,
        ip_address INET,
        user_agent TEXT,
        started_at TIMESTAMP DEFAULT NOW(),
        ended_at TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE
    )
    """)

    # Create system_metrics table for performance monitoring
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS system_metrics (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        metric_type VARCHAR NOT NULL,
        metric_value NUMERIC,
        metric_unit VARCHAR,
        labels JSONB,
        recorded_at TIMESTAMP DEFAULT NOW()
    )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_last_login ON users(last_login)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invites_token_hash ON invites(token_hash)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invites_expires_at ON invites(expires_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invites_used ON invites(used)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_actor_id ON audit_logs(actor_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_uploaded_by ON documents(uploaded_by)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_uploaded_at ON documents(uploaded_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_metadata_gin ON documents USING GIN (metadata)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks(doc_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_chunk_index ON chunks(chunk_index)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_qa_sessions_user_id ON qa_sessions(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_qa_sessions_timestamp ON qa_sessions(timestamp)")

    # Create partial indexes for better performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_pending_review ON documents(status) WHERE status = 'pending_review'")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_active ON documents(status) WHERE status = 'active'")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invites_active ON invites(expires_at, used) WHERE used = FALSE AND expires_at > NOW()")

    # Create composite indexes for common query patterns
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_uploaded_by_status ON documents(uploaded_by, status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_uploaded_at_status ON documents(uploaded_at, status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_actor_action ON audit_logs(actor_id, action)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_qa_sessions_user_timestamp ON qa_sessions(user_id, timestamp)")

    # Indexes for analytics tables
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics_events_user_id ON analytics_events(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics_events_event_type ON analytics_events(event_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics_events_created_at ON analytics_events(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics_events_user_type ON analytics_events(user_id, event_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics_events_session_id ON analytics_events(session_id)")

    # Indexes for document collaboration tables
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_document_versions_doc_id ON document_versions(doc_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_document_versions_created_at ON document_versions(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_document_comments_doc_id ON document_comments(doc_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_document_comments_parent ON document_comments(parent_comment_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_document_comments_author ON document_comments(author_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_document_comments_resolved ON document_comments(is_resolved)")

    # Indexes for session tracking
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions(is_active)")

    # Indexes for system metrics
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_system_metrics_type ON system_metrics(metric_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_system_metrics_recorded_at ON system_metrics(recorded_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_system_metrics_type_time ON system_metrics(metric_type, recorded_at)")

    # Insert default superadmin user if not exists
    cursor.execute("SELECT id FROM users WHERE email='superadmin@company.com'")
    if not cursor.fetchone():
        cursor.execute("""
        INSERT INTO users (email, password_hash, role, is_active)
        VALUES (%s, %s, %s, %s)
        """, ("superadmin@company.com", hash_password("SuperAdmin123!"), "superadmin", True))

    conn.commit()
    conn.close()
    logger.info("Auth DB initialized with new schema.")

def authenticate_user(email: str, password: str):
    try:
        conn = psycopg2.connect(POSTGRES_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, password_hash, role, is_active FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        conn.close()
        if user and check_password(password, user[2]) and user[4]:  # Check is_active
            return {"user_id": str(user[0]), "email": user[1], "role": user[3], "is_active": user[4]}
        return None
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return None

def generate_tokens(user_data:dict) -> tuple:
    access_payload = {
        "email": user_data["email"],
        "role": user_data["role"],
        "user_id": user_data["user_id"],
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXP_MINUTES)
    }

    refresh_payload = {
        "email": user_data["email"],
        "exp": datetime.utcnow() + timedelta(days=REFRESH_EXP_DAYS)
    }
    access_token = jwt.encode(access_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    refresh_token = jwt.encode(refresh_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return access_token, refresh_token


def store_refresh_token(email:str, refresh_token:str):
    hashed_refresh = hash_password(refresh_token)
    conn = psycopg2.connect(POSTGRES_URL)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET refresh_token = %s WHERE email = %s", (hashed_refresh, email))
    conn.commit()
    conn.close()

def refresh_access_token(refresh_token: str):
    decoded_token = jwt.decode(refresh_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    email = decoded_token.get("email")
    conn = psycopg2.connect(POSTGRES_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT refresh_token, role, id FROM users WHERE email=%s", (email,))
    stored_hash = cursor.fetchone()
    conn.close()
    if not stored_hash or not check_password(refresh_token, stored_hash[0]):
        raise ValueError("Invalid refresh token")
    new_access_payload = {
        "email": email,
        "role": stored_hash[1],
        "user_id": str(stored_hash[2]),
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXP_MINUTES)
    }

    return jwt.encode(new_access_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def revoke_token(token:str):
    redis = Redis(url=REDIS_URL, token=REDIS_TOKEN)
    decoded = jwt.decode(token,JWT_SECRET,algorithms=[JWT_ALGORITHM],options={"verify_exp":False})
    exp = decoded.get("exp",0) - int(datetime.utcnow().timestamp())
    redis.setex(f"blacklist:{token}",exp if exp > 0 else 3600 , "revoked")

def is_token_revoked(token:str) -> bool:
    redis = Redis(url=REDIS_URL, token=REDIS_TOKEN)
    return redis.exists(f"blacklist:{token}") > 0

def decode_jwt(token:str) -> dict:
    if is_token_revoked(token):
        raise ValueError("Token revoked")
    return jwt.decode(token,JWT_SECRET,algorithms=[JWT_ALGORITHM])

def check_rate_limit(user_id: str, limit_per_min: int = RATE_LIMIT_PER_MIN) -> bool:
    redis = Redis(url=REDIS_URL, token=REDIS_TOKEN)
    key = f"rate:{user_id}"
    current_time = int(datetime.utcnow().timestamp())
    window_start = current_time - 60  # 1 minute window

    # Use sorted set to track timestamps
    redis.zadd(key, {str(current_time): current_time})
    redis.zremrangebyscore(key, 0, window_start)  # Remove old entries
    count = redis.zcard(key)

    # Set expiration for cleanup
    redis.expire(key, 120)  # Expire after 2 minutes

    return count <= limit_per_min


def require_auth(request: Request) -> dict:
    """Dependency to require authentication. Decodes and validates JWT from Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid")

    token = auth_header.split(" ")[1]
    try:
        payload = decode_jwt(token)
        # Load user from DB and check is_active
        conn = psycopg2.connect(POSTGRES_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, role, is_active FROM users WHERE id = %s", (payload["user_id"],))
        user = cursor.fetchone()
        conn.close()

        if not user or not user[3]:  # Check is_active
            raise HTTPException(status_code=401, detail="User not found or inactive")

        return {
            "user_id": str(user[0]),
            "email": user[1],
            "role": user[2],
            "is_active": user[3]
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


def require_role(allowed_roles: list) -> callable:
    """Dependency factory to require specific roles. Supports scoped roles like 'admin:hr'."""
    def role_checker(user: dict = Depends(require_auth)) -> dict:
        user_role = user["role"]

        # Check if user has superadmin (can access all)
        if user_role == "superadmin":
            return user

        # Check if user role is in allowed roles
        if user_role in allowed_roles:
            return user

        # Check for scoped roles (e.g., 'admin:hr' allows 'admin:hr', 'admin:compliance', etc.)
        for allowed_role in allowed_roles:
            if allowed_role.startswith(user_role.split(':')[0] + ':'):
                return user

        raise HTTPException(status_code=403, detail=f"Insufficient permissions. Required: {allowed_roles}")

    return role_checker


def setup_mfa(user_id: str) -> dict:
    """Generate MFA secret and QR code for user."""
    if not PYOTP_AVAILABLE:
        raise HTTPException(status_code=500, detail="MFA not available")

    # Generate TOTP secret
    secret = pyotp.random_base32()

    # Generate backup codes
    backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]

    # Update user in database
    conn = psycopg2.connect(POSTGRES_URL)
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE users SET mfa_secret = %s, backup_codes = %s WHERE id = %s
    """, (secret, backup_codes, user_id))
    conn.commit()
    conn.close()

    # Generate provisioning URI for QR code
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(name=f"AstraRAG:{user_id}", issuer_name="AstraRAG")

    return {
        "secret": secret,
        "provisioning_uri": provisioning_uri,
        "backup_codes": backup_codes
    }


def verify_mfa(user_id: str, code: str) -> bool:
    """Verify MFA code or backup code."""
    if not PYOTP_AVAILABLE:
        return False

    conn = psycopg2.connect(POSTGRES_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT mfa_secret, backup_codes FROM users WHERE id = %s", (user_id,))
    result = cursor.fetchone()
    conn.close()

    if not result:
        return False

    secret, backup_codes = result

    # Check TOTP code
    if secret:
        totp = pyotp.TOTP(secret)
        if totp.verify(code):
            return True

    # Check backup codes
    if backup_codes and code in backup_codes:
        # Remove used backup code
        backup_codes.remove(code)
        conn = psycopg2.connect(POSTGRES_URL)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET backup_codes = %s WHERE id = %s", (backup_codes, user_id))
        conn.commit()
        conn.close()
        return True

    return False


def enable_mfa(user_id: str) -> bool:
    """Enable MFA for user after successful setup."""
    conn = psycopg2.connect(POSTGRES_URL)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET mfa_enabled = TRUE WHERE id = %s", (user_id,))
    conn.commit()
    conn.close()
    return True


def create_invite(email: str, role: str, created_by: str, ip: Optional[str] = None) -> str:
    """Create a new invite token. Returns the raw token."""
    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_password(raw_token)
    expires_at = datetime.utcnow() + timedelta(hours=24)  # 24 hours

    conn = psycopg2.connect(POSTGRES_URL)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO invites (email, token_hash, role, created_by, expires_at)
    VALUES (%s, %s, %s, %s, %s)
    RETURNING id
    """, (email, token_hash, role, created_by, expires_at))
    invite_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()

    # Audit log
    log_audit_event(
        actor_id=created_by,
        action="invite_created",
        target=str(invite_id),
        meta={"email": email, "role": role},
        ip=ip
    )

    return raw_token


def validate_invite_token(raw_token: str, email: str) -> dict:
    """Validate invite token and return invite details if valid."""
    token_hash = hash_password(raw_token)

    conn = psycopg2.connect(POSTGRES_URL)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, email, role, created_by, expires_at, used
    FROM invites
    WHERE token_hash = %s AND email = %s
    """, (token_hash, email))
    invite = cursor.fetchone()
    conn.close()

    if not invite:
        raise HTTPException(status_code=400, detail="Invalid invite token or email")

    invite_id, invite_email, role, created_by, expires_at, used = invite

    if used:
        raise HTTPException(status_code=400, detail="Invite token already used")

    if datetime.utcnow() > expires_at:
        raise HTTPException(status_code=400, detail="Invite token expired")

    return {
        "invite_id": str(invite_id),
        "email": invite_email,
        "role": role,
        "created_by": str(created_by)
    }


def register_user(email: str, password: str, invite_token: str, ip: Optional[str] = None) -> dict:
    """Register a new user with invite validation."""
    if not validate_password_policy(password):
        raise HTTPException(status_code=400, detail="Password does not meet security requirements")

    invite_data = validate_invite_token(invite_token, email)

    # Create user
    password_hash = hash_password(password)
    conn = psycopg2.connect(POSTGRES_URL)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO users (email, password_hash, role, is_active)
    VALUES (%s, %s, %s, %s)
    RETURNING id
    """, (email, password_hash, invite_data["role"], True))
    user_id = cursor.fetchone()[0]

    # Mark invite as used
    cursor.execute("""
    UPDATE invites SET used = TRUE, used_by = %s WHERE id = %s
    """, (user_id, invite_data["invite_id"]))

    conn.commit()
    conn.close()

    # Audit log
    log_audit_event(
        actor_id=invite_data["created_by"],
        action="user_created",
        target=str(user_id),
        meta={"invite_id": invite_data["invite_id"], "role": invite_data["role"]},
        ip=ip
    )

    return {"user_id": str(user_id), "email": email, "role": invite_data["role"]}