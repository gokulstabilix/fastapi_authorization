from datetime import datetime
from typing import Tuple

from sqlalchemy.orm import Session

from authorization_service.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from authorization_service.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def authenticate(self, *, email: str, password: str):
        user = self.users.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def issue_tokens(self, *, user_id: int) -> Tuple[str, datetime, str, datetime]:
        access_token, access_expires = create_access_token(subject=str(user_id))
        refresh_token, refresh_expires = create_refresh_token(subject=str(user_id))
        return access_token, access_expires, refresh_token, refresh_expires

    def refresh_access_token(self, *, refresh_token: str) -> Tuple[str, datetime, int]:
        payload = verify_token(refresh_token, token_type="refresh")
        user_id = int(payload.sub)
        # optional: ensure user exists
        user = self.users.get(user_id)
        if not user:
            return None, None, None
        access_token, access_expires = create_access_token(subject=str(user.id))
        return access_token, access_expires, user.id
