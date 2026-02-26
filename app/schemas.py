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
