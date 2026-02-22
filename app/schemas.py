from typing import Optional

from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str
    email: str
    age: int 
    password:str

class UserResponse(UserCreate):
    id:int
    name:str
    email:str
    age:Optional[int]=None
    
    class Config:
        from_attributes = True
