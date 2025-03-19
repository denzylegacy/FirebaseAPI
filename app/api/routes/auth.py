# -*- coding: utf-8 -*-

from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Any, Dict
import secrets
from pydantic import BaseModel
import uuid

from app.api.models.schemas import Token, User, UserCreate, UserResponse
from app.api.security.jwt import (
    authenticate_user, create_access_token, get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.api.security.password import get_password_hash
from app.settings import log
from app.services.email_client.async_gmail import async_gmail_client
from firebase_admin.exceptions import FirebaseError
from app.services import async_firebase
from app.settings import CONFIG
from app.services.firebase_client.async_firebase import AsyncFirebase

router = APIRouter()

password_reset_tokens = {}

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login", response_model=Token)
async def login(login_data: OAuth2PasswordRequestForm = Depends()):
    """
    Get access token with email and password
    """
    await log.async_info(f"Login endpoint called with username: {login_data.username}")
    
    user = await authenticate_user(login_data.username, login_data.password)
    if not user:
        await log.async_warning(f"Failed login attempt for email: {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    access_token = create_access_token(
        data={
            "sub": user.email, 
            "user_id": user.id,
            "is_admin": user.is_admin  # Include is_admin in token
        },
        expires_delta=access_token_expires
    )
    
    await log.async_info(f"User with email {login_data.username} logged in successfully")
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/user/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)) -> Any:
    """
    Get current user information
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User information
    """
    return current_user

@router.post("/forgot-password", response_model=dict)
async def request_password_reset(email: str) -> Dict[str, str]:
    """
    Request password reset for an account
    
    Args:
        email: User's email address
        
    Returns:
        Success message
    """
    try:
        users_data = await async_firebase.read("users")
        user_id = None
        user_data = None
        
        if users_data:
            for uid, user_info in users_data.items():
                if user_info.get("email") == email:
                    user_id = uid
                    user_data = user_info
                    break
        
        if not user_id or not user_data:
            # Don't reveal that email doesn't exist for security reasons
            await log.async_warning(f"Password reset requested for non-existent email: {email}")
            return {"message": "If your email is registered, you'll receive a password reset link"}
        
        # Generate secure token
        token = secrets.token_urlsafe(32)
        expires = datetime.utcnow() + timedelta(hours=1)
        
        # Store token (in a real app, store in database)
        password_reset_tokens[token] = {
            "user_id": user_id,
            "email": email,
            "expires": expires
        }
        
        # Create reset link
        reset_link = f"{CONFIG.BASE_URL}/reset-password?token={token}"
        
        # Send email
        reset_html = f"""
        <html>
          <body>
            <h1>Password Reset</h1>
            <p>Hello {user_data.get('username')},</p>
            <p>You requested a password reset. Click the link below to reset your password:</p>
            <p><a href="{reset_link}">Reset Password</a></p>
            <p>This link is valid for 1 hour.</p>
            <p>If you didn't request this, please ignore this email.</p>
          </body>
        </html>
        """
        
        await async_gmail_client.send_html_email(
            subject="Password Reset Request",
            html_body=reset_html,
            recipients=[email]
        )
        
        await log.async_info(f"Password reset link sent to {email}")
        return {"message": "If your email is registered, you'll receive a password reset link"}
    
    except Exception as e:
        await log.async_error(f"Error sending password reset email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process password reset request"
        )

@router.post("/reset-password", response_model=dict)
async def reset_password(token: str, new_password: str) -> Dict[str, str]:
    """
    Reset password using token
    
    Args:
        token: Reset token from email
        new_password: New password
        
    Returns:
        Success message
    """
    # Validate token
    if token not in password_reset_tokens:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )
    
    token_data = password_reset_tokens[token]
    
    # Check expiration
    if datetime.utcnow() > token_data["expires"]:
        # Remove expired token
        del password_reset_tokens[token]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token has expired"
        )
    
    try:
        # Update password in Firebase
        user_id = token_data["user_id"]
        hashed_password = get_password_hash(new_password)
        
        # Get current user data
        user_data = await async_firebase.read(f"users/{user_id}")
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update password
        user_data["hashed_password"] = hashed_password
        success = await async_firebase.update(f"users/{user_id}", user_data)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )
        
        # Remove used token
        del password_reset_tokens[token]
        
        # Send confirmation email
        confirm_html = f"""
        <html>
          <body>
            <h1>Password Reset Complete</h1>
            <p>Your password has been successfully reset.</p>
            <p>If you didn't make this change, please contact support immediately.</p>
          </body>
        </html>
        """
        
        await async_gmail_client.send_html_email(
            subject="Password Reset Complete",
            html_body=confirm_html,
            recipients=[token_data["email"]]
        )
        
        await log.async_info(f"Password reset completed for user {user_id}")
        return {"message": "Password has been reset successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        await log.async_error(f"Error resetting password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )

@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def register(user_data: UserCreate):
    """
    Register a new user
    """
    try:
        # Check if email already exists
        users_data = await async_firebase.read("users")
        if users_data:
            for _, data in users_data.items():
                if data.get("email") == user_data.email:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already registered"
                    )
        
        # Hash the password
        hashed_password = get_password_hash(user_data.password)
        
        # Generate a unique user ID
        user_id = str(uuid.uuid4())
        
        # Create user data with is_admin field (default to False)
        new_user = {
            "username": user_data.username,
            "email": user_data.email,
            "hashed_password": hashed_password,
            "disabled": False,
            "is_admin": False  # Default to non-admin
        }
        
        # Save to Firebase
        await async_firebase.create(f"users/{user_id}", new_user)
        
        return {
            "id": user_id,
            "username": user_data.username,
            "email": user_data.email,
            "is_active": True
        }
    except HTTPException:
        raise
    except Exception as e:
        await log.async_error(f"Error registering user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register user: {str(e)}"
        )

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()) -> Any:
    """
    Get access token with email and password
    """
    await log.async_info(f"Login attempt with username: {form_data.username}")
    
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        await log.async_warning(f"Failed login attempt for email: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=access_token_expires,
    )
    
    await log.async_info(f"User with email {form_data.username} logged in successfully")
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login-json", response_model=Token)
async def login_json(login_data: LoginRequest):
    """
    Get access token with email and password (JSON version)
    """
    await log.async_info(f"Login endpoint called with email: {login_data.email}")
    
    user = await authenticate_user(login_data.email, login_data.password)
    if not user:
        await log.async_warning(f"Failed login attempt for email: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    access_token = create_access_token(
        data={
            "sub": user.email, 
            "user_id": user.id,
            "is_admin": user.is_admin
        },
        expires_delta=access_token_expires
    )
    
    await log.async_info(f"User with email {login_data.email} logged in successfully")
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/check-admin", response_model=Dict[str, Any])
async def check_admin():
    """
    Check if admin user exists (public endpoint for testing)
    """
    try:
        # Create an instance
        firebase = AsyncFirebase()
        admin_data = await firebase.read("users/admin")
        if not admin_data:
            return {"exists": False}
        
        # Don't return sensitive data
        return {
            "exists": True,
            "email": admin_data.get("email"),
            "username": admin_data.get("username"),
            "is_admin": admin_data.get("is_admin", False)
        }
    except Exception as e:
        await log.async_error(f"Error checking admin: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check admin: {str(e)}"
        )

@router.get("/test", response_model=Dict[str, str])
async def test_endpoint():
    """
    Test endpoint (public)
    """
    return {"message": "API is working!"}

@router.get("/test-firebase", response_model=Dict[str, Any])
async def test_firebase():
    """
    Test Firebase connection
    """
    try:
        firebase = AsyncFirebase()
        connection_ok = await firebase.test_connection()
        
        if connection_ok:
            return {"status": "ok", "message": "Firebase connection successful"}
        else:
            return {"status": "error", "message": "Firebase connection failed"}
    except Exception as e:
        await log.async_error(f"Error testing Firebase connection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test Firebase connection: {str(e)}"
        )
