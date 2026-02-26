# OAuth2 Implementation Guide

## Overview

This FastAPI backend now supports two authentication methods:
1. **Standard Login** - Email/Password authentication with regular users
2. **OAuth2 (Google)** - Social login using Google Sign-In with a separate OAuthUser table

## Database Structure

### Standard Users Table (`users`)
- Stores users who sign up with email/password
- Includes full profile information from signup
- Password is hashed with Argon2

### OAuth Users Table (`oauth_users`)
- Stores users who sign in via Google OAuth
- Minimal required fields: `email`, `firstName`, `provider_id`
- Optional fields can be filled later: `phone`, `age`, `bloodGroup`, etc.
- Tracks `created_at` and `last_login` timestamps
- Stores provider info (Google, Facebook, etc.) for future multi-provider support

## API Endpoints

### Authentication Endpoints

#### Standard Login
```
POST /login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=password123

Response:
{
    "access_token": "eyJ0eXAiOiJKV1QiLC...",
    "token_type": "bearer",
    "user_type": "standard"
}
```

#### Standard Signup
```
POST /signup
Content-Type: application/json

{
    "firstName": "John",
    "lastName": "Doe",
    "email": "john@example.com",
    "phone": "+91 98765 43210",
    "dateOfBirth": "1995-01-01",
    "age": 29,
    "gender": "Male",
    "bloodGroup": "O+",
    "address": "123 Street",
    "city": "Mumbai",
    "state": "Maharashtra",
    "zipCode": "400001",
    "emergencyContactName": "Jane Doe",
    "emergencyContactPhone": "+91 98765 43211",
    "password": "securepassword123"
}

Response:
{
    "message": "User created successfully"
}
```

#### Google OAuth Login
```
POST /auth/google
Content-Type: application/json

{
    "idToken": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjE..."
}

Response:
{
    "access_token": "eyJ0eXAiOiJKV1QiLC...",
    "token_type": "bearer",
    "user_type": "oauth"
}
```

### Profile Endpoint

#### Get User Profile
```
GET /profile
Headers:
Authorization: Bearer <access_token>

Response:
{
    "id": 1,
    "firstName": "John",
    "lastName": "Doe",
    "email": "john@example.com",
    "age": 29,
    "phone": "+91 98765 43210",
    "bloodGroup": "O+",
    "gender": "Male",
    "address": "123 Street",
    "city": "Mumbai",
    "picture": "https://...",  // Only in OAuth response
    "provider": "google",       // Only in OAuth response
    "user_type": "standard" or "oauth"
}
```

## Mobile Integration (React Native)

### Using Google Sign-In with OAuth Endpoint

```javascript
// import { GoogleSignin } from '@react-native-google-signin/google-signin';
// import AsyncStorage from '@react-native-async-storage/async-storage';

// GoogleSignin.configure({
//     webClientId: 'YOUR_WEB_CLIENT_ID.apps.googleusercontent.com',
//     offlineAccess: true,
// });

// const handleGoogleSignIn = async () => {
//     try {
//         await GoogleSignin.hasPlayServices();
//         const userInfo = await GoogleSignin.signIn();
//         const { idToken } = userInfo;

//         // Send ID token to backend
//         const response = await fetch('http://192.168.1.8:8000/auth/google', {
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             body: JSON.stringify({ idToken })
//         });

//         const data = await response.json();
        
//         if (response.ok) {
//             await AsyncStorage.setItem('jwtToken', data.access_token);
//             await AsyncStorage.setItem('userType', data.user_type);
//             navigation.navigate('HomeScreen');
//         }
//     } catch (err) {
//         console.error('Google Sign-In Error:', err);
//     }
// };
```

## How It Works

### Standard Login Flow
1. User enters email and password
2. Backend verifies credentials against `users` table
3. JWT token is created with `type: "standard"`
4. Frontend stores token in AsyncStorage

### OAuth2 Google Login Flow
1. User clicks "Sign in with Google"
2. Google Sign-In SDK returns ID token to mobile app
3. Mobile app sends ID token to `/auth/google` endpoint
4. Backend verifies the ID token structure
5. Backend creates/updates user in `oauth_users` table
6. JWT token is created with `type: "oauth"`
7. Frontend stores token in AsyncStorage
8. Profile endpoint recognizes OAuth users and returns available data

### Token Verification
- Both token types use JWT with HS256 algorithm
- Tokens expire after 30 minutes (configurable)
- Profile endpoint works seamlessly with both user types

## Security Considerations

### Production Checklist
- [ ] Set `SECRET_KEY` from environment variable
- [ ] Verify Google tokens with Google's API (currently just decodes)
- [ ] Use HTTPS in production
- [ ] Implement rate limiting on auth endpoints
- [ ] Use bcrypt instead of argon2 if compatibility issues arise
- [ ] Set proper CORS origins (not `["*"]`)
- [ ] Store OAuth tokens if refresh flows need to be supported

### Current Limitations
- Google tokens are decoded but not verified against Google's API
- No refresh token mechanism for OAuth users
- No support for other OAuth providers yet (easily extensible)

## Database Setup

After updating models, run migrations:

```python
from app.database import engine
from app import models

# This creates all tables
models.Base.metadata.create_all(bind=engine)
```

Or with Alembic:
```bash
alembic revision --autogenerate -m "Add OAuthUser table"
alembic upgrade head
```

## Testing

### Test Standard Login
```bash
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=password123"
```

### Test OAuth Login (with mock ID token)
```bash
curl -X POST http://localhost:8000/auth/google \
  -H "Content-Type: application/json" \
  -d '{
    "idToken": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

### Get Profile
```bash
curl -X GET http://localhost:8000/profile \
  -H "Authorization: Bearer <access_token>"
```

## Future Enhancements

1. **Multi-Provider OAuth** - Add Facebook, GitHub, Apple Sign-In
2. **Refresh Tokens** - Implement token refresh mechanism
3. **User Profile Updates** - Allow OAuth users to complete profile info
4. **Account Linking** - Link OAuth accounts with existing email accounts
5. **Token Verification** - Properly verify Google tokens via Google API
