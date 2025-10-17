import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
import psycopg2
import secrets

from fastapi import Depends, HTTPException, Request
from pydantic import BaseModel

from backend.shared.database.db import get_db_connection
from backend.shared.utils.security import hash_password, check_password, validate_password_policy
from backend.shared.utils.auth import decode_jwt
from config.config import JWT_SECRET, JWT_EXP_MINUTES, REFRESH_EXP_DAYS

logger = logging.getLogger(__name__)

# MFA imports
try:
    import pyotp
    PYOTP_AVAILABLE = True
except ImportError:
    logger.warning("pyotp not available, MFA disabled")
    pyotp = None
    PYOTP_AVAILABLE = False

JWT_ALGORITHM = "HS256"

def authenticate_user(email: str, password: str):
    try:
        conn = get_db_connection()
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

def generate_tokens(user_data: dict) -> tuple:
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
    access_token = jwt.encode(access_payload, JWT_SECRET or "", algorithm=JWT_ALGORITHM)
    refresh_token = jwt.encode(refresh_payload, JWT_SECRET or "", algorithm=JWT_ALGORITHM)
    return access_token, refresh_token

def store_refresh_token(email: str, refresh_token: str):
    hashed_refresh = hash_password(refresh_token)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET refresh_token = %s WHERE email = %s", (hashed_refresh, email))
    conn.commit()
    conn.close()

def refresh_access_token(refresh_token: str):
    decoded_token = jwt.decode(refresh_token, JWT_SECRET or "", algorithms=[JWT_ALGORITHM])
    email = decoded_token.get("email")
    conn = get_db_connection()
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

    return jwt.encode(new_access_payload, JWT_SECRET or "", algorithm=JWT_ALGORITHM)

def revoke_token(token: str):
    # Implementation would use Redis or similar
    pass

def is_token_revoked(token: str) -> bool:
    # Implementation would use Redis or similar
    return False

def check_rate_limit(user_id: str, limit_per_min: int = 100) -> bool:
    # Implementation would use Redis or similar
    return True

def require_auth(request: Request) -> dict:
    """Dependency to require authentication. Decodes and validates JWT from Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid")

    token = auth_header.split(" ")[1]
    try:
        payload = decode_jwt(token)
        # Load user from DB and check is_active
        conn = get_db_connection()
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

def require_role(allowed_roles: list):
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
    import pyotp
    secret = pyotp.random_base32()

    # Generate backup codes
    backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]

    # Update user in database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE users SET mfa_secret = %s, backup_codes = %s WHERE id = %s
    """, (secret, backup_codes, user_id))
    conn.commit()
    conn.close()

    # Generate provisioning URI for QR code
    import pyotp
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

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT mfa_secret, backup_codes FROM users WHERE id = %s", (user_id,))
    result = cursor.fetchone()
    conn.close()

    if not result:
        return False

    secret, backup_codes = result

    # Check TOTP code
    if secret:
        import pyotp
        totp = pyotp.TOTP(secret)
        if totp.verify(code):
            return True

    # Check backup codes
    if backup_codes and code in backup_codes:
        # Remove used backup code
        backup_codes.remove(code)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET backup_codes = %s WHERE id = %s", (backup_codes, user_id))
        conn.commit()
        conn.close()
        return True

    return False

def enable_mfa(user_id: str) -> bool:
    """Enable MFA for user after successful setup."""
    conn = get_db_connection()
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

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO invites (email, token_hash, role, created_by, expires_at)
    VALUES (%s, %s, %s, %s, %s)
    RETURNING id
    """, (email, token_hash, role, created_by, expires_at))
    result = cursor.fetchone()
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create invite")
    invite_id = result[0]
    conn.commit()
    conn.close()

    return raw_token

def validate_invite_token(raw_token: str, email: str) -> dict:
    """Validate invite token and return invite details if valid."""
    token_hash = hash_password(raw_token)

    conn = get_db_connection()
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
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO users (email, password_hash, role, is_active)
    VALUES (%s, %s, %s, %s)
    RETURNING id
    """, (email, password_hash, invite_data["role"], True))
    result = cursor.fetchone()
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create user")
    user_id = result[0]

    # Mark invite as used
    cursor.execute("""
    UPDATE invites SET used = TRUE, used_by = %s WHERE id = %s
    """, (user_id, invite_data["invite_id"]))

    conn.commit()
    conn.close()

    return {"user_id": str(user_id), "email": email, "role": invite_data["role"]}