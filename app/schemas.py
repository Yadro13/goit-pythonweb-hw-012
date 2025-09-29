from datetime import date, datetime
from typing import Optional, Annotated, TypeAlias, Literal
from pydantic import BaseModel, EmailStr, Field, StringConstraints

# Явные алиасы типов вместо constr(...), а то ругается что не соответствует рекомендациям в Pydantic v2
PhoneStr: TypeAlias = Annotated[str, StringConstraints(min_length=5, max_length=50)]
PasswordStr: TypeAlias = Annotated[str, StringConstraints(min_length=8, max_length=128)]

# --- Users ---
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: PasswordStr  # было: constr(min_length=8, max_length=128)

class UserOut(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"   # можно оставить просто str = "bearer"
    refresh_token: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# --- Contacts ---
class ContactBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: PhoneStr            # было: PhoneStr через constr
    birthday: date
    extra: Optional[str] = None

class ContactCreate(ContactBase):
    pass

class ContactUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[PhoneStr] = None
    birthday: Optional[date] = None
    extra: Optional[str] = None

class ContactOut(ContactBase):
    id: int
    created_at: datetime
    updated_at: datetime
    owner_id: int
    class Config:
        from_attributes = True
