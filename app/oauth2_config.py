"""
OAuth2 Configuration for Google Sign-In Integration
"""
from dotenv import load_dotenv
import os
# Google OAuth2 Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

load_dotenv()
# List of allowed origins for CORS
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://192.168.1.8:8000",
]

# Token settings
TOKEN_EXPIRE_MINUTES = 30
ALGORITHM = "HS256"
SECRET_KEY = "supersecretkey"  # Change to environment variable in production

# OAuth Provider URLs (for future reference)
GOOGLE_TOKEN_ENDPOINT = os.getenv("GOOGLE_TOKEN_ENDPOINT")
GOOGLE_USERINFO_ENDPOINT = os.getenv("GOOGLE_USERINFO_ENDPOINT")
