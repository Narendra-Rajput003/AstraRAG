import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

from backend.services.auth_service.api import (
    authenticate_user, generate_tokens, store_refresh_token, require_auth, require_role,
    create_invite, register_user, setup_mfa, verify_mfa, enable_mfa, refresh_access_token
)
from backend.services.auth_service.models import (
    LoginRequest, RegisterRequest, MFASetupRequest, MFAVerifyRequest, 
    TokensResponse, UserResponse, LoginResponseWithMFA, InviteRequest
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthResponse(BaseModel):
    status: str
    timestamp: str

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

@app.post("/login", response_model=LoginResponseWithMFA)
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
            # In a real implementation, you would use a proper JWT library
            temp_token = "temp_mfa_token_placeholder"

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
        # In a real implementation, you would update the database

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

@app.post("/register")
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

@app.post("/refresh")
async def refresh_token(refresh_token: str):
    """Refresh access token using refresh token."""
    try:
        new_access_token = refresh_access_token(refresh_token)
        return {"access_token": new_access_token}
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@app.post("/mfa/setup")
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

@app.post("/mfa/verify")
async def verify_user_mfa(request: MFAVerifyRequest, user: dict = Depends(require_auth)):
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

@app.post("/invite")
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

@app.get("/validate")
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)