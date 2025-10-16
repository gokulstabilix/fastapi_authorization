from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union, Tuple

from jose import jwt, JWTError
from passlib.context import CryptContext

from authorization_service.core.config import settings
from authorization_service.schemas.token import TokenPayload

pwd_context = CryptContext(
    schemes=["bcrypt_sha256", "bcrypt"],  # prefer bcrypt_sha256; still accept legacy bcrypt
    deprecated="auto",
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_token(
    subject: Union[str, int], 
    token_type: str = "access",
    expires_delta: Optional[timedelta] = None
) -> Tuple[str, datetime]:
    """
    Create a JWT token with the given subject and type.
    
    Args:
        subject: The subject of the token (usually user ID)
        token_type: Type of token ('access' or 'refresh')
        expires_delta: Optional timedelta for token expiration
    
    Returns:
        Tuple of (encoded_token, expiration_datetime)
    """
    if expires_delta is None:
        if token_type == "refresh":
            expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        else:
            expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "exp": expire
    }
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt, expire


def create_access_token(subject: Union[str, int]) -> Tuple[str, datetime]:
    """Create an access token with default expiration."""
    return create_token(subject, "access")


def create_refresh_token(subject: Union[str, int]) -> Tuple[str, datetime]:
    """Create a refresh token with default expiration."""
    return create_token(subject, "refresh")


def verify_token(token: str, token_type: str = "access") -> TokenPayload:
    """
    Verify a JWT token and return its payload if valid.
    
    Args:
        token: The JWT token to verify
        token_type: Expected token type ('access' or 'refresh')
        
    Returns:
        TokenPayload if token is valid
        
    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        if token_type and payload.get("type") != token_type:
            raise JWTError("Invalid token type")
            
        return TokenPayload(**payload)
    except JWTError as e:
        raise JWTError("Invalid token") from e
