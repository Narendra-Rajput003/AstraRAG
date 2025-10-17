import jwt
from config.config import JWT_SECRET

JWT_ALGORITHM = "HS256"

def decode_jwt(token: str) -> dict:
    """Decode and validate a JWT token."""
    return jwt.decode(token, JWT_SECRET or "", algorithms=[JWT_ALGORITHM])

def is_token_revoked(token: str) -> bool:
    """Check if a token has been revoked."""
    # In a real implementation, this would check a revocation list (Redis, database, etc.)
    return False