from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TokenBase(BaseModel):
    token_type: str = "bearer"
    expires_at: Optional[datetime] = None


class Token(TokenBase):
    access_token: str
    access_token_expires_in: int


class TokenWithRefresh(Token):
    refresh_token: str
    refresh_token_expires_in: int


class TokenPayload(BaseModel):
    sub: str
    type: Optional[str] = None
    exp: Optional[datetime] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=10)
