from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    organization_slug: str = "northstar"


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict
    organization: dict
