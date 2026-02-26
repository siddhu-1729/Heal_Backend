from sqlalchemy import Column, Integer, String, Date, DateTime
from datetime import datetime
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
    created_at = Column(DateTime, default=datetime.utcnow)
    # confirmPassword = Column(String)

class OAuthUser(Base):
    __tablename__ = "oauth_users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    firstName = Column(String, index=True)
    lastName = Column(String, index=True, nullable=True)
    picture = Column(String, nullable=True)  # profile picture URL from OAuth provider
    provider = Column(String, index=True)  # 'google', 'facebook', etc.
    provider_id = Column(String, unique=True, index=True)  # unique ID from OAuth provider
    phone = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    bloodGroup = Column(String, nullable=True)
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    zipCode = Column(String, nullable=True)
    emergencyContactName = Column(String, nullable=True)
    emergencyContactPhone = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow)

