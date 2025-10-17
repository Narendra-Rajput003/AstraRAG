from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class User(BaseModel):
    id: str
    email: str
    role: str
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    invite_token: str
    email: str
    password: str

class MFASetupRequest(BaseModel):
    code: str

class MFAVerifyRequest(BaseModel):
    code: str

class TokensResponse(BaseModel):
    access_token: str
    refresh_token: str

class UserResponse(BaseModel):
    user_id: str
    username: str
    role: str
    organization_id: int

class LoginResponseWithMFA(BaseModel):
    user: UserResponse
    tokens: Optional[TokensResponse] = None
    mfa_required: bool = False
    temp_token: Optional[str] = None

class InviteRequest(BaseModel):
    email: str
    role: str