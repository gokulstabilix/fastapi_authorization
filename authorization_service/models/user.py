from sqlalchemy import Column, Integer, String, DateTime, Boolean, func,Index

from authorization_service.db.base_class import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(320), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Email verification and OTP fields
    is_email_verified = Column(Boolean, nullable=False, default=False)
    email_otp_hash = Column(String(255), nullable=True)
    email_otp_expires_at = Column(DateTime(timezone=True), nullable=True)
    email_otp_attempts = Column(Integer, nullable=False, default=0)
    email_otp_last_sent_at = Column(DateTime(timezone=True), nullable=True)


   
    __table_args__ = (
        Index("ix_unverified_users_created_at", "is_email_verified", "created_at"),
    )