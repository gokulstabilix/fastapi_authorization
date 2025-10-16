from collections.abc import Generator

from sqlalchemy.orm import Session

from authorization_service.db.session import SessionLocal
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from authorization_service.core.config import settings
from authorization_service.models.user import User
from authorization_service.repositories.user_repository import UserRepository


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


token_auth_scheme = HTTPBearer()


def get_current_user(
    token: str = Depends(token_auth_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        subject: str | None = payload.get("sub")
        if subject is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user_repo = UserRepository(db)
    user: User | None
    if subject.isdigit():
        user = user_repo.get(int(subject))
    else:
        user = user_repo.get_by_email(subject)

    if user is None:
        raise credentials_exception
    return user
