import sys
import os
import logging
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import jwt
import psycopg2
from passlib.hash import bcrypt
import pyotp

# Add project root to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.config import POSTGRES_URL, REDIS_URL, REDIS_TOKEN, JWT_SECRET, JWT_EXP_MINUTES, REFRESH_EXP_DAYS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

JWT_ALGORITHM = "HS256"

# Database connection
def get_db_connection():
    return psycopg2.connect(POSTGRES_URL)

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    invite_token: str
    email: str
    password: str

class InviteRequest(BaseModel):
    email: str
    role: str

class MFAVerifyRequest(BaseModel):
    code: str

class UserResponse(BaseModel):
    user_id: str
    username: str
    role: str
    organization_id: int

class TokensResponse(BaseModel):
    access_token: str
    refresh_token: str

class LoginResponseWithMFA(BaseModel):
    user: UserResponse
    tokens: Optional[TokensResponse] = None
    mfa_required: bool = False
    temp_token: Optional[str] = None

def hash_password(password: str) -> str:
    return bcrypt.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.verify(password, hashed)

def generate_tokens(user_data: Dict[str, Any]) -> tuple[str, str]:
    """Generate access and refresh tokens."""
    access_payload = {
        "user_id": str(user_data["user_id"]),
        "email": user_data["email"],
        "role": user_data["role"],
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXP_MINUTES),
        "iat": datetime.utcnow(),
        "type": "access"
    }

    refresh_payload = {
        "user_id": str(user_data["user_id"]),
        "email": user_data["email"],
        "exp": datetime.utcnow() + timedelta(days=REFRESH_EXP_DAYS),
        "iat": datetime.utcnow(),
        "type": "refresh"
    }

    access_token = jwt.encode(access_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    refresh_token = jwt.encode(refresh_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return access_token, refresh_token

def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate user with email and password."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT id, email, password_hash, role, is_active, mfa_enabled, mfa_secret, backup_codes
        FROM users WHERE email = %s AND is_active = true
        """, (email,))

        user = cursor.fetchone()
        conn.close()

        if user and verify_password(password, user[2]):
            return {
                "user_id": user[0],
                "email": user[1],
                "role": user[3],
                "is_active": user[4],
                "mfa_enabled": user[5],
                "mfa_secret": user[6],
                "backup_codes": user[7] or []
            }

        return None

    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return None

def validate_invite_token(token: str, email: str) -> Optional[Dict[str, Any]]:
    """Validate invite token."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Hash the token for comparison
        token_hash = hash_password(token)

        cursor.execute("""
        SELECT id, email, role, created_by, expires_at
        FROM invites
        WHERE email = %s AND token_hash = %s AND used = false AND expires_at > NOW()
        """, (email, token_hash))

        invite = cursor.fetchone()
        conn.close()

        if invite:
            return {
                "invite_id": invite[0],
                "email": invite[1],
                "role": invite[2],
                "created_by": invite[3]
            }

        return None

    except Exception as e:
        logger.error(f"Invite validation error: {e}")
        return None

def create_invite(email: str, role: str, created_by: str, client_ip: Optional[str] = None) -> str:
    """Create a new user invite."""
    import secrets

    token = secrets.token_urlsafe(32)
    token_hash = hash_password(token)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO invites (email, token_hash, role, created_by, expires_at)
        VALUES (%s, %s, %s, %s, NOW() + INTERVAL '7 days')
        """, (email, token_hash, role, created_by))

        conn.commit()
        conn.close()

        logger.info(f"Invite created for {email} by {created_by}")
        return token

    except Exception as e:
        logger.error(f"Invite creation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

def register_user(email: str, password: str, invite_token: str, client_ip: Optional[str] = None) -> Dict[str, Any]:
    """Register a new user with invite token."""
    # Validate invite
    invite_data = validate_invite_token(invite_token, email)
    if not invite_data:
        raise HTTPException(status_code=400, detail="Invalid or expired invite token")

    # Hash password
    password_hash = hash_password(password)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Create user
        cursor.execute("""
        INSERT INTO users (email, password_hash, role, department)
        VALUES (%s, %s, %s, %s)
        RETURNING id, email, role
        """, (email, password_hash, invite_data["role"], "General"))

        user = cursor.fetchone()

        # Mark invite as used
        cursor.execute("""
        UPDATE invites SET used = true, used_by = %s WHERE id = %s
        """, (user[0], invite_data["invite_id"]))

        conn.commit()
        conn.close()

        logger.info(f"User registered: {email}")
        return {
            "user_id": str(user[0]),
            "email": user[1],
            "role": user[2]
        }

    except Exception as e:
        logger.error(f"User registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

def setup_mfa(user_id: str) -> Dict[str, Any]:
    """Setup MFA for user."""
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(name=f"AstraRAG:{user_id}", issuer_name="AstraRAG")

    # Generate backup codes
    backup_codes = [pyotp.random_base32()[:8] for _ in range(10)]

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE users SET mfa_secret = %s, backup_codes = %s WHERE id = %s
        """, (secret, backup_codes, user_id))

        conn.commit()
        conn.close()

        return {
            "provisioning_uri": provisioning_uri,
            "backup_codes": backup_codes
        }

    except Exception as e:
        logger.error(f"MFA setup error: {e}")
        raise HTTPException(status_code=500, detail="MFA setup failed")

def verify_mfa(user_id: str, code: str) -> bool:
    """Verify MFA code or backup code."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT mfa_secret, backup_codes FROM users WHERE id = %s
        """, (user_id,))

        user = cursor.fetchone()
        if not user:
            return False

        mfa_secret, backup_codes = user

        # Check TOTP code
        if mfa_secret:
            totp = pyotp.TOTP(mfa_secret)
            if totp.verify(code):
                conn.close()
                return True

        # Check backup codes
        if backup_codes and code in backup_codes:
            # Remove used backup code
            backup_codes.remove(code)
            cursor.execute("""
            UPDATE users SET backup_codes = %s WHERE id = %s
            """, (backup_codes, user_id))
            conn.commit()
            conn.close()
            return True

        conn.close()
        return False

    except Exception as e:
        logger.error(f"MFA verification error: {e}")
        return False

def enable_mfa(user_id: str):
    """Enable MFA for user."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE users SET mfa_enabled = true WHERE id = %s
        """, (user_id,))

        conn.commit()
        conn.close()

    except Exception as e:
        logger.error(f"MFA enable error: {e}")
        raise HTTPException(status_code=500, detail="Failed to enable MFA")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Auth service startup")
    yield
    logger.info("Auth service shutdown")

app = FastAPI(
    title="Auth Service",
    description="Authentication and user management microservice",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "auth-service",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/auth/login")
async def login(request: LoginRequest):
    """User login endpoint."""
    logger.info(f"Login attempt for user: {request.email}")

    user_data = authenticate_user(request.email, request.password)
    if not user_data:
        logger.warning(f"Failed login attempt for user: {request.email}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Check if MFA is required
    mfa_required = user_data["role"] in ["admin", "superadmin"]

    if mfa_required and user_data.get("mfa_enabled", False):
        # Generate temporary token for MFA verification
        temp_payload = {
            "email": user_data["email"],
            "user_id": str(user_data["user_id"]),
            "mfa_pending": True,
            "exp": datetime.utcnow() + timedelta(minutes=5)
        }
        temp_token = jwt.encode(temp_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        logger.info(f"MFA required for user: {request.email}")
        return LoginResponseWithMFA(
            user=UserResponse(
                user_id=str(user_data["user_id"]),
                username=user_data["email"],
                role=user_data["role"],
                organization_id=1
            ),
            mfa_required=True,
            temp_token=temp_token
        )

    # No MFA required
    access_token, refresh_token = generate_tokens(user_data)

    # Update last login
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET last_login = NOW() WHERE id = %s", (user_data["user_id"],))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"Failed to update last login: {e}")

    logger.info(f"Successful login for user: {request.email}")
    return LoginResponseWithMFA(
        user=UserResponse(
            user_id=str(user_data["user_id"]),
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

@app.post("/auth/register")
async def register(request: RegisterRequest, req: Request = None):
    """User registration endpoint."""
    client_ip = req.client.host if req else None
    user_data = register_user(request.email, request.password, request.invite_token, client_ip)
    return {"message": "User registered successfully", "user": user_data}

@app.post("/admin/invite")
async def create_user_invite(request: InviteRequest, req: Request = None):
    """Create user invite (requires authentication in gateway)."""
    # This would be validated by gateway, but we include basic auth check
    client_ip = req.client.host if req else None

    # For microservices, we assume gateway handles auth
    # In production, implement proper inter-service auth
    raw_token = create_invite(request.email, request.role, "system", client_ip)
    return {"message": "Invite created", "email": request.email, "token": raw_token}

@app.get("/admin/invites")
async def list_invites():
    """List all invites."""
    try:
        conn = get_db_connection()
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
                "created_by": str(invite[3]) if invite[3] else None,
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
async def revoke_invite(invite_id: str, req: Request = None):
    """Revoke an invite."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE invites SET expires_at = NOW() WHERE id = %s AND used = FALSE
        RETURNING id
        """, (invite_id,))

        result = cursor.fetchone()
        conn.commit()
        conn.close()

        if not result:
            raise HTTPException(status_code=404, detail="Invite not found or already used")

        return {"message": "Invite revoked successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking invite: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/auth/mfa/setup")
async def setup_user_mfa(req: Request = None):
    """Setup MFA (user ID from gateway auth)."""
    # In microservices, user ID comes from gateway
    user_id = req.headers.get("X-User-ID") if req else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    mfa_data = setup_mfa(user_id)
    return {
        "message": "MFA setup initiated",
        "provisioning_uri": mfa_data["provisioning_uri"],
        "backup_codes": mfa_data["backup_codes"]
    }

@app.post("/auth/mfa/verify")
async def verify_user_mfa(request: MFAVerifyRequest, req: Request = None):
    """Verify MFA setup."""
    user_id = req.headers.get("X-User-ID") if req else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    if verify_mfa(user_id, request.code):
        enable_mfa(user_id)
        return {"message": "MFA enabled successfully"}
    else:
        raise HTTPException(status_code=400, detail="Invalid MFA code")

@app.post("/auth/mfa/authenticate")
async def authenticate_mfa(request: MFAVerifyRequest, req: Request = None):
    """Verify MFA during login."""
    user_id = req.headers.get("X-User-ID") if req else None
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    if verify_mfa(user_id, request.code):
        return {"message": "MFA authentication successful"}
    else:
        raise HTTPException(status_code=400, detail="Invalid MFA code")

@app.get("/auth/validate")
async def validate_token_endpoint(req: Request = None):
    """Validate current access token."""
    user_id = req.headers.get("X-User-ID") if req else None
    user_email = req.headers.get("X-User-Email") if req else None
    user_role = req.headers.get("X-User-Role") if req else None

    if not all([user_id, user_email, user_role]):
        raise HTTPException(status_code=401, detail="Invalid token")

    return {
        "valid": True,
        "user": {
            "user_id": user_id,
            "email": user_email,
            "role": user_role,
            "is_active": True
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)