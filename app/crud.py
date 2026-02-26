from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from . import models, schemas
from datetime import datetime

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(
        firstName=user.firstName,
        lastName=user.lastName,
        email=user.email,
        phone=user.phone,
        age=user.age,
        gender=user.gender,
        bloodGroup=user.bloodGroup,
        address=user.address,
        city=user.city,
        state=user.state,
        zipCode=user.zipCode,
        emergencyContactName=user.emergencyContactName,
        emergencyContactPhone=user.emergencyContactPhone,
        password=user.password,
        created_at=datetime.utcnow()
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_users(db: Session):
    return db.query(models.User).all()

def create_or_update_oauth_user(db: Session, email: str, firstName: str, lastName: str = None, 
                                 picture: str = None, provider: str = "google", provider_id: str = None):
    """Create or update OAuthUser"""
    existing_user = db.query(models.OAuthUser).filter(models.OAuthUser.email == email).first()
    
    if existing_user:
        # Update last_login
        existing_user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(existing_user)
        return existing_user
    
    # Create new OAuth user
    oauth_user = models.OAuthUser(
        email=email,
        firstName=firstName,
        lastName=lastName,
        picture=picture,
        provider=provider,
        provider_id=provider_id,
        created_at=datetime.utcnow(),
        last_login=datetime.utcnow()
    )
    db.add(oauth_user)
    db.commit()
    db.refresh(oauth_user)
    return oauth_user

from datetime import datetime, timedelta
from jose import jwt

SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

