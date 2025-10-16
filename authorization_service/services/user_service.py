from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from authorization_service.core.config import settings
from authorization_service.core.security import get_password_hash, verify_password
from authorization_service.repositories.user_repository import UserRepository
from authorization_service.schemas.user import UserCreate
from authorization_service.utils.email import send_verification_otp_email
from authorization_service.utils.otp import generate_numeric_otp
from authorization_service.models.user import User


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    # Queries
    def get_by_email(self, email: str) -> Optional[User]:
        return self.users.get_by_email(email)

    def get(self, id: int) -> Optional[User]:
        return self.users.get(id)

    # Registration
    def register(self, user_in: UserCreate) -> User:
        existing = self.users.get_by_email(user_in.email)
        if existing:
            raise ValueError("Email already registered")
        hashed_password = get_password_hash(user_in.password)
        user = self.users.create_user(
            email=user_in.email,
            full_name=user_in.full_name,
            hashed_password=hashed_password,
        )
        return user

    # OTP helpers
    def can_resend_email_otp(self, user: User) -> bool:
        if not user.email_otp_last_sent_at:
            return True
        now = datetime.now(timezone.utc)
        delta = now - user.email_otp_last_sent_at
        return delta.total_seconds() >= settings.EMAIL_OTP_RESEND_INTERVAL_SECONDS

    def set_email_otp(self, user: User, otp: str) -> User:
        now = datetime.now(timezone.utc)
        user.email_otp_hash = get_password_hash(otp)
        user.email_otp_expires_at = now + timedelta(minutes=settings.EMAIL_OTP_EXPIRE_MINUTES)
        user.email_otp_attempts = 0
        user.email_otp_last_sent_at = now
        return self.users.update(user)

    def verify_email_otp(self, user: User, otp: str) -> bool:
        # Check expiry
        now = datetime.now(timezone.utc)
        if not user.email_otp_expires_at or user.email_otp_expires_at < now:
            return False
        # Check attempts
        if user.email_otp_attempts >= settings.EMAIL_OTP_MAX_ATTEMPTS:
            return False
        ok = False
        if user.email_otp_hash and verify_password(otp, user.email_otp_hash):
            ok = True
        if ok:
            user.is_email_verified = True
            user.email_otp_hash = None
            user.email_otp_expires_at = None
            user.email_otp_attempts = 0
            user.email_otp_last_sent_at = None
        else:
            user.email_otp_attempts += 1
        self.users.update(user)
        return ok

    # High-level flows
    def send_verification_otp(self, email: str) -> None:
        user = self.users.get_by_email(email)
        if not user:
            raise LookupError("User not found")
        if user.is_email_verified:
            raise RuntimeError("Email already verified")
        if not self.can_resend_email_otp(user):
            raise TimeoutError("OTP recently sent. Please wait before requesting again.")
        otp = generate_numeric_otp()
        user = self.set_email_otp(user, otp)
        send_verification_otp_email(to_email=user.email, otp=otp)
