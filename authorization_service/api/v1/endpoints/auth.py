from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Security, Request
from sqlalchemy.orm import Session
from jose import JWTError

from authorization_service.api.deps import get_db
from authorization_service.schemas.token import Token, TokenWithRefresh, RefreshTokenRequest
from authorization_service.core.config import settings
from authorization_service.schemas.login import LoginRequest
from authorization_service.schemas.otp import SendOtpRequest, VerifyOtpRequest
from authorization_service.services.auth_service import AuthService
from authorization_service.services.user_service import UserService
from authorization_service.core.rate_limiter import limiter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenWithRefresh)
@limiter.limit(settings.RATE_LIMIT_LOGIN, key_func=lambda: "auth_login")
async def login_access_token(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db),
):
    auth = AuthService(db)
    user = auth.authenticate(email=login_data.email, password=login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
    if not user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email using the OTP sent to you.",
        )
    # Issue tokens
    access_token, access_token_expires, refresh_token, refresh_token_expires = auth.issue_tokens(user_id=user.id)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "access_token_expires_in": int((access_token_expires - datetime.now(access_token_expires.tzinfo)).total_seconds()),
        "expires_at": access_token_expires.isoformat(),
        "refresh_token": refresh_token,
        "refresh_token_expires_in": int((refresh_token_expires - datetime.now(refresh_token_expires.tzinfo)).total_seconds())
    }


@router.post("/refresh-token", response_model=Token)
@limiter.limit(settings.RATE_LIMIT_REFRESH, key_func=lambda: "auth_refresh")
async def refresh_access_token(
    request: Request,
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """
    Refresh an access token using a refresh token.
    """
    auth = AuthService(db)
    try:
        access_token, access_token_expires, user_id = auth.refresh_access_token(refresh_token=payload.refresh_token)
        if not access_token:
            # user not found or invalid
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "access_token_expires_in": int((access_token_expires - datetime.now(access_token_expires.tzinfo)).total_seconds()),
            "expires_at": access_token_expires.isoformat()
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/send-otp")
@limiter.limit(settings.RATE_LIMIT_SEND_OTP, key_func=lambda: "auth_send_otp")
async def send_verification_otp(
    request: Request,
    payload: SendOtpRequest, 
    db: Session = Depends(get_db)
):
    users = UserService(db)
    try:
        users.send_verification_otp(payload.email)
        return {"message": "OTP sent"}
    except LookupError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except RuntimeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already verified")
    except TimeoutError:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="OTP recently sent. Please wait before requesting again.")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to send email: {e}")


@router.post("/verify-otp")
@limiter.limit(settings.RATE_LIMIT_VERIFY_OTP, key_func=lambda: "auth_verify_otp")
async def verify_verification_otp(
    request: Request,
    payload: VerifyOtpRequest, 
    db: Session = Depends(get_db)
):
    users = UserService(db)
    user = users.get_by_email(payload.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.is_email_verified:
        return {"message": "Email already verified"}

    ok = users.verify_email_otp(user, payload.otp)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP")
    return {"message": "Email verified successfully"}
