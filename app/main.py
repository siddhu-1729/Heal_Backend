from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from datetime import timedelta

from app.oauth2_config import GOOGLE_CLIENT_ID
from app.security import hash_password, verify_password
from . import models, schemas, crud
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/users", response_model=list[schemas.UserResponse])
def read_users(db: Session = Depends(get_db)):
    return crud.get_users(db)

# ── Standard Login/Signup ──
@app.post("/signup")
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pw = hash_password(user.password)
    db_user = models.User(
        firstName=user.firstName,
        lastName=user.lastName,
        email=user.email,
        phone=user.phone,
        dateOfBirth=user.dateOfBirth,
        age=user.age,
        gender=user.gender,
        bloodGroup=user.bloodGroup,
        address=user.address,
        city=user.city,
        state=user.state,
        zipCode=user.zipCode,
        emergencyContactName=user.emergencyContactName,
        emergencyContactPhone=user.emergencyContactPhone,
        password=hashed_pw
    )
    db.add(db_user)
    db.commit()
    return {"message": "User created successfully"}


from fastapi.security import OAuth2PasswordRequestForm

@app.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(
        models.User.email == form_data.username
    ).first()

    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = crud.create_access_token({"sub": user.email, "type": "standard"})
    return {"access_token": token, "token_type": "bearer", "user_type": "standard"}


# ── OAuth2 Google Login ──
from google.oauth2 import id_token
from google.auth.transport import requests
from fastapi import HTTPException


def verify_google_token(token: str) -> dict:
    try:
        payload = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            GOOGLE_CLIENT_ID
        )

        # Verify issuer
        if payload['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise HTTPException(status_code=401, detail="Invalid issuer")

        return payload

    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google token")


@app.post("/auth/google", response_model=schemas.TokenResponse)
def google_login(
    request: schemas.GoogleTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Google OAuth2 login endpoint.
    Expects Google ID token from frontend (from google-signin library).
    """
    try:
        # Verify the Google ID token
        payload = verify_google_token(request.idToken)
        
        email = payload.get('email')
        first_name = payload.get('given_name', 'User')
        last_name = payload.get('family_name', '')
        picture = payload.get('picture')
        provider_id = payload.get('sub')
        
        # Create or update OAuth user in database
        oauth_user = crud.create_or_update_oauth_user(
            db=db,
            email=email,
            firstName=first_name,
            lastName=last_name,
            picture=picture,
            provider="google",
            provider_id=provider_id
        )
        
        # Generate access token
        token = crud.create_access_token({
            "sub": oauth_user.email,
            "type": "oauth",
            "provider": "google",
            "user_id": oauth_user.id
        })
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_type": "oauth"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/profile", response_model=dict)
def profile(current_user: str = Depends(crud.get_current_user), db: Session = Depends(get_db)):
    """
    Get user profile - supports both standard and OAuth users.
    """
    # Try standard user first
    user = db.query(models.User).filter(models.User.email == current_user).first()
    if user:
        return {
            "id": user.id,
            "firstName": user.firstName,
            "lastName": user.lastName,
            "email": user.email,
            "age": user.age,
            "phone": user.phone,
            "bloodGroup": user.bloodGroup,
            "gender": user.gender,
            "address": user.address,
            "city": user.city,
            "state": user.state,
            "zipCode": user.zipCode,
            "emergencyContactName": user.emergencyContactName,
            "emergencyContactPhone": user.emergencyContactPhone,
            "user_type": "standard"
        }
    
    # Try OAuth user
    oauth_user = db.query(models.OAuthUser).filter(models.OAuthUser.email == current_user).first()
    if oauth_user:
        return {
            "id": oauth_user.id,
            "firstName": oauth_user.firstName,
            "lastName": oauth_user.lastName,
            "email": oauth_user.email,
            "age": oauth_user.age,
            "phone": oauth_user.phone,
            "bloodGroup": oauth_user.bloodGroup,
            "gender": oauth_user.gender,
            "address": oauth_user.address,
            "city": oauth_user.city,
            "picture": oauth_user.picture,
            "provider": oauth_user.provider,
            "user_type": "oauth"
        }
    
    raise HTTPException(status_code=404, detail="User not found")

