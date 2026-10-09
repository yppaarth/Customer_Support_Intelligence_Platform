from datetime import datetime, timedelta, timezone
from typing import Annotated

from argon2 import PasswordHasher
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.enums import Role
from app.models.organization import OrganizationMembership, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except Exception:
        return False


def create_access_token(user_id: str, organization_id: str, role: str) -> str:
    settings = get_settings()
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": user_id, "org": organization_id, "role": role, "exp": expires}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


class Principal:
    def __init__(self, user: User, organization_id: str, role: str):
        self.user = user
        self.organization_id = organization_id
        self.role = role

    def can_write_tickets(self) -> bool:
        return self.role in {Role.ORG_ADMIN, Role.SUPPORT_MANAGER, Role.SUPPORT_AGENT}

    def can_manage_users(self) -> bool:
        return self.role == Role.ORG_ADMIN

    def can_review(self) -> bool:
        return self.role in {Role.ORG_ADMIN, Role.SUPPORT_MANAGER, Role.SUPPORT_AGENT}


def get_current_principal(
    request: Request,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> Principal:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        user_id = str(payload["sub"])
        organization_id = str(payload["org"])
    except (JWTError, KeyError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.scalar(select(User).where(User.id == user_id, User.is_active.is_(True)))
    membership = db.scalar(
        select(OrganizationMembership).where(
            OrganizationMembership.user_id == user_id,
            OrganizationMembership.organization_id == organization_id,
        )
    )
    if not user or not membership:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Membership not found")

    request.state.organization_id = organization_id
    request.state.user_id = user_id
    return Principal(user=user, organization_id=organization_id, role=membership.role)


def require_roles(*roles: Role):
    def dependency(principal: Annotated[Principal, Depends(get_current_principal)]) -> Principal:
        if principal.role not in set(roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return principal

    return dependency
