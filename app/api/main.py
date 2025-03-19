# -*- coding: utf-8 -*-

import time
import random
import os
import warnings
import json

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message=".*bcrypt.*")
warnings.filterwarnings("ignore", message=".*error reading bcrypt version.*")

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import status
from contextlib import asynccontextmanager
from passlib.context import CryptContext

load_dotenv()

from app.api.middleware.rate_limiter import RateLimitMiddleware
from app.api.middleware.auth import AuthMiddleware
from app.api.routes import data, auth
from app.settings import log, CONFIG
from app.services.firebase_client.async_firebase import AsyncFirebase
from app.api.security.password import get_password_hash


firebase = AsyncFirebase()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup and handle cleanup on shutdown"""
    try:
        await firebase._initialize_firebase()
        
        admin_password = os.getenv("ADMIN_PASSWORD", "admin")  # Default password if not provided
        
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed_password = pwd_context.hash(admin_password)
        
        await log.async_info("Admin password hashed successfully")
        
        await firebase.ensure_default_entry("users", {
            "admin": {
                "username": CONFIG.ADMIN_USERNAME,
                "email": CONFIG.ADMIN_EMAIL,
                "hashed_password": hashed_password,
                "disabled": CONFIG.ADMIN_DISABLED,
                "is_admin": True
            }
        })
        
        await log.async_info("API started successfully")
    except Exception as e:
        await log.async_error(f"Error during startup: {e}")
    
    yield
    
    # Shutdown code (if any)
    # Add cleanup code here if needed


app = FastAPI(
    title="Secure Firebase API",
    description="Secure API for CRUD operations on Firebase",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CONFIG.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware, rate=CONFIG.RATE_LIMIT_RATE, per=CONFIG.RATE_LIMIT_PER)
# Comment out the authentication middleware for testing
# app.add_middleware(AuthMiddleware)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(data.router, prefix="/api/v1/data", tags=["Data"])


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log request details and timing"""
    request_id = random.randint(1, 10000000000000000000)
    await log.async_info(f"Request {request_id} - {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        
        if response.status_code >= 400:
            await log.async_warning(f"Request {request_id} completed with status code {response.status_code}")
        else:
            await log.async_info(f"Request {request_id} completed with status code {response.status_code}")
            
        return response
    except Exception as e:
        await log.async_error(f"Request {request_id} failed: {str(e)}")
        
        # await log.async_error(f"Unhandled exception: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": "Internal server error",
                "detail": str(e) if app.debug else "An unexpected error occurred"
            }
        )


@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "firebase-api"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions"""
    await log.async_error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."}
    )


@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    await log.async_info("API starting up...")
    
    await firebase.initialize()
    
    # Check if admin user exists
    users_data = await firebase.read("users")
    await log.async_info(f"Users data at startup: {json.dumps(users_data, indent=2)}")
    
    admin_exists = False
    
    if users_data:
        for user_id, user_data in users_data.items():
            if user_data.get("email") == CONFIG.ADMIN_EMAIL:
                admin_exists = True
                await log.async_info(f"Admin user found: {user_id}")
                if not user_data.get("is_admin", False):
                    user_data["is_admin"] = True
                    await firebase.write(f"users/{user_id}", user_data)
                    await log.async_info(f"Updated admin privileges for user: {CONFIG.ADMIN_EMAIL}")
                break
    
    if not admin_exists:
        admin_user = {
            "username": CONFIG.ADMIN_USERNAME,
            "email": CONFIG.ADMIN_EMAIL,
            "hashed_password": get_password_hash(CONFIG.ADMIN_PASSWORD),
            "disabled": CONFIG.ADMIN_DISABLED,
            "is_admin": True
        }
        
        await firebase.write("users/admin", admin_user)
        await log.async_info(f"Created admin user: {CONFIG.ADMIN_EMAIL}")
    
    await log.async_info("API started successfully")
