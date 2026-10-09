from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.organization import Organization, OrganizationMembership, User
from app.schemas.auth import AuthResponse, LoginRequest
from app.security.auth import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    settings = get_settings()
    if settings.is_production and settings.demo_login_enabled:
        raise HTTPException(status_code=500, detail="Demo login must be disabled in production")
    user = db.scalar(select(User).where(User.email == payload.email, User.is_active.is_(True)))
    org = db.scalar(select(Organization).where(Organization.slug == payload.organization_slug))
    if not user or not org or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    membership = db.scalar(
        select(OrganizationMembership).where(
            OrganizationMembership.user_id == user.id,
            OrganizationMembership.organization_id == org.id,
        )
    )
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No organization membership")
    return AuthResponse(
        access_token=create_access_token(user.id, org.id, membership.role),
        user={"id": user.id, "email": user.email, "full_name": user.full_name, "role": membership.role},
        organization={"id": org.id, "name": org.name, "slug": org.slug},
    )
