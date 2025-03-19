# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.settings import CONFIG, log
from app.api.models.schemas import User, UserInDB
from app.services.firebase_client.async_firebase import AsyncFirebase


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
firebase = AsyncFirebase()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Get password hash"""
    return pwd_context.hash(password)


async def get_user(username: str) -> Optional[UserInDB]:
    """Get user from Firebase"""
    users_data = await firebase.read("users")
    if not users_data:
        return None
        
    for user_id, user_data in users_data.items():
        if user_data.get("username") == username:
            return UserInDB(**user_data)
    
    return None


async def authenticate_user(email: str, password: str) -> Optional[User]:
    """
    Authenticate a user with email and password using Firebase Authentication
    """
    await log.async_info(f"Attempting to authenticate user: {email}")
    
    try:
        users_data = await firebase.read("users")
        await log.async_info(f"Users data: {users_data}")
        
        user_data = None
        user_id = None
        
        if users_data:
            for uid, data in users_data.items():
                await log.async_info(f"Checking user {uid}: {data}")
                if data.get("email") == email:
                    user_data = data
                    user_id = uid
                    await log.async_info(f"User data found: {user_data}")
                    break
        
        if not user_data or "hashed_password" not in user_data:
            await log.async_warning(f"User data not found or incomplete: {email}")
            return None
        
        stored_hash = user_data["hashed_password"]
        
        is_valid = verify_password(password, stored_hash)
        await log.async_info(f"Password valid: {is_valid}")
        
        if not is_valid:
            await log.async_warning(f"Invalid password for user: {email}")
            return None
        
        return User(
            id=user_id,
            email=email,
            username=user_data.get("username", ""),
            is_active=not user_data.get("disabled", False)
        )
            
    except Exception as e:
        await log.async_error(f"Authentication error: {str(e)}")
        return None


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, CONFIG.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, CONFIG.SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        
        if email is None or user_id is None:
            raise credentials_exception
            
        if user_id == "admin":
            return User(
                id="admin",
                email=CONFIG.ADMIN_EMAIL,
                username=CONFIG.ADMIN_USERNAME,
                is_active=not CONFIG.ADMIN_DISABLED
            )
        
        users_data = await firebase.read("users")
        user_data = None
        
        if users_data:
            for uid, data in users_data.items():
                if data.get("email") == email:
                    user_data = data
                    break
        
        if not user_data:
            raise credentials_exception
            
        return User(
            id=user_id,
            email=email,
            username=user_data.get("username", ""),
            is_active=True
        )
        
    except JWTError:
        raise credentials_exception


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
