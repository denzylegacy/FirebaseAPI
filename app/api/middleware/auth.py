# -*- coding: utf-8 -*-

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from jose import jwt
from typing import List, Optional
from starlette.responses import JSONResponse

from app.settings import CONFIG, log
from app.api.security.jwt import ALGORITHM


PUBLIC_PATHS = [
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/auth/login",
    "/api/v1/auth/token",
    "/api/v1/auth/register",
    "/api/v1/auth/forgot-password",
    "/api/v1/health",
    "/favicon.ico",
    "/health"
]


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware to check authentication for protected routes"""
    
    def __init__(self, app, exclude_paths: Optional[List[str]] = None):
        """
        Initialize authentication middleware
        
        Args:
            app: FastAPI application
            exclude_paths: List of paths to exclude from authentication check
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or PUBLIC_PATHS
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Process request through authentication middleware
        
        Args:
            request: FastAPI request
            call_next: Next middleware/endpoint
            
        Returns:
            Response or authentication error
        """
        # public paths that don't require authentication
        public_paths = [
            "/api/v1/health",
            "/api/v1/auth/login",
            "/api/v1/auth/login-json",
            "/api/v1/auth/register",
            "/api/v1/auth/token",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
        
        path = request.url.path
        if any(path.startswith(public_path) for public_path in public_paths):
            await log.async_info(f"Skipping authentication for public path: {path}")
            return await call_next(request)
        
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            await log.async_warning(f"Unauthorized access attempt to {path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "status": "error",
                    "message": "Not authenticated",
                    "detail": "Authentication credentials were not provided or are invalid"
                }
            )
        
        try:
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, CONFIG.SECRET_KEY, algorithms=[ALGORITHM])
            username: str | None = payload.get("sub", None)
            
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
                
            request.state.user = username
            request.state.user_id = payload.get("user_id")
            
            return await call_next(request)
        except Exception as e:
            await log.async_warning(f"Unauthorized access attempt to {path}")
            await log.async_error(f"Authentication error: {str(e)}")
            
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "status": "error",
                    "message": "Not authenticated",
                    "detail": "Authentication credentials were not provided or are invalid"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )
