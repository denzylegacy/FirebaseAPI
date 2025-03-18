# -*- coding: utf-8 -*-

import time
from typing import Dict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
from fastapi.responses import JSONResponse

from app.settings import log


class RateLimiter:
    """Rate limiter implementation using token bucket algorithm"""
    
    def __init__(self, rate: int, per: int):
        """
        Initialize rate limiter
        
        Args:
            rate: Number of requests allowed per time period
            per: Time period in seconds
        """
        self.rate = rate  # Number of tokens per time period
        self.per = per    # Time period in seconds
        self.token_bucket: Dict[str, Dict[str, float]] = {}
        self.last_refill: Dict[str, float] = {}
    
    def _get_tokens(self, key: str) -> Dict[str, float]:
        """Get token bucket for key, initializing if it doesn't exist"""
        if key not in self.token_bucket:
            self.token_bucket[key] = {"tokens": float(self.rate), "last_refill": time.time()}
        return self.token_bucket[key]
    
    def _refill_bucket(self, key: str) -> None:
        """Refill token bucket based on elapsed time"""
        bucket = self._get_tokens(key)
        now = time.time()
        time_passed = now - bucket["last_refill"]
        new_tokens = time_passed * (self.rate / self.per)
        
        # Update bucket
        bucket["tokens"] = min(self.rate, bucket["tokens"] + new_tokens)
        bucket["last_refill"] = now
    
    async def is_allowed(self, key: str) -> bool:
        """
        Check if request is allowed based on rate limit
        
        Args:
            key: Identifier for the client (IP, user ID, etc.)
            
        Returns:
            True if allowed, False if rate limited
        """
        self._refill_bucket(key)
        bucket = self._get_tokens(key)
        
        if bucket["tokens"] >= 1:
            bucket["tokens"] -= 1
            return True
        else:
            return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to apply rate limiting to API requests"""
    
    def __init__(self, app, rate: int = 60, per: int = 60):
        """
        Initialize rate limit middleware
        
        Args:
            app: FastAPI application
            rate: Number of requests allowed per time period
            per: Time period in seconds
        """
        super().__init__(app)
        self.limiter = RateLimiter(rate, per)
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Process request through rate limiter
        
        Args:
            request: FastAPI request
            call_next: Next middleware/endpoint
            
        Returns:
            Response or rate limit error
        """
        # Extract client identifier (IP or user ID if authenticated)
        client_ip = request.client.host if request.client else "unknown"
        # We could use a more complex key combining IP and endpoint for more granular control
        
        # Check if client is allowed based on rate limit
        if await self.limiter.is_allowed(client_ip):
            response = await call_next(request)
            return response
        else:
            await log.async_warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Please try again later."
                }
            ) 