from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict, Field


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    # Using bcrypt_sha256 for hashing removes the 72-byte bcrypt limit; allow longer passwords
    password: str = Field(min_length=6, max_length=512)

class UserRead(UserBase):
    id: int
    created_at: datetime
    is_email_verified: bool

    model_config = ConfigDict(from_attributes=True)
