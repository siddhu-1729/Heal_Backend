from sqlalchemy import Column, Integer, String , Date
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    firstName = Column(String, index=True)
    lastName = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, index=True)
    dateOfBirth = Column(Date)
    age = Column(Integer)
    gender = Column(String)
    bloodGroup = Column(String)
    address = Column(String)
    city = Column(String)
    state = Column(String)
    zipCode = Column(String)
    emergencyContactName = Column(String)
    emergencyContactPhone = Column(String)
    password = Column(String)
    # confirmPassword = Column(String)

