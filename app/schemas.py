from typing import Optional

from pydantic import BaseModel , EmailStr
from datetime import date

class UserCreate(BaseModel):
    firstName: str
    lastName: str
    email: EmailStr
    phone: str
    dateOfBirth: date
    age: int
    gender: str
    bloodGroup: str
    address: str
    city: str
    state: str
    zipCode: str
    emergencyContactName: str
    emergencyContactPhone: str
    password: str
    # confirmPassword: str


class UserResponse(UserCreate):
    id:int
    firstName:str
    lastName:str
    email:str
    age:Optional[int]=None
    phone:str
    bloodGroup:str
    gender:str
    address:str
    city:str
    emergencyContactName:str
    emergencyContactPhone:str

    class Config:
        from_attributes = True


# OAuth Schemas
class GoogleTokenRequest(BaseModel):
    """Google OAuth ID token received from frontend"""
    idToken: str


class OAuthUserResponse(BaseModel):
    """Response for OAuth authenticated user"""
    id: int
    email: str
    firstName: str
    lastName: Optional[str] = None
    picture: Optional[str] = None
    provider: str
    phone: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    bloodGroup: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str
    user_type: str  # 'oauth' or 'standard'
