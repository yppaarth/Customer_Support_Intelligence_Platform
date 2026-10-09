from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.security.auth import Principal, get_current_principal

DbDep = Annotated[Session, Depends(get_db)]
PrincipalDep = Annotated[Principal, Depends(get_current_principal)]
