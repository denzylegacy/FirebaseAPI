# -*- coding: utf-8 -*-

import os
import logging
from dataclasses import dataclass
from typing import List


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

log = logging.getLogger("firebase-api")


class AsyncLogger:
    """Async wrapper for standard logger"""
    
    def __init__(self, logger):
        self.logger = logger
    
    async def async_log(self, level, msg, *args, **kwargs):
        """Async log method"""
        self.logger.log(level, msg, *args, **kwargs)
    
    async def async_debug(self, msg, *args, **kwargs):
        """Async debug log method"""
        self.logger.debug(msg, *args, **kwargs)
    
    async def async_info(self, msg, *args, **kwargs):
        """Async info log method"""
        self.logger.info(msg, *args, **kwargs)
    
    async def async_warning(self, msg, *args, **kwargs):
        """Async warning log method"""
        self.logger.warning(msg, *args, **kwargs)
    
    async def async_error(self, msg, *args, **kwargs):
        """Async error log method"""
        self.logger.error(msg, *args, **kwargs)
    
    async def async_critical(self, msg, *args, **kwargs):
        """Async critical log method"""
        self.logger.critical(msg, *args, **kwargs)


log = AsyncLogger(log)


@dataclass
class FirebaseConfig:
    """Firebase configuration"""
    FIREBASE_API_KEY: str
    FIREBASE_URL: str
    FIREBASE_CERT_FILE_PATH: str


@dataclass
class Config:
    """Application configuration"""
    ENVIRONMENT: str
    DEBUG: bool
    SECRET_KEY: str
    CORS_ORIGINS: List[str]
    RATE_LIMIT_RATE: int
    RATE_LIMIT_PER: int
    FIREBASE: FirebaseConfig
    ADMIN_USERNAME: str
    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str
    ADMIN_DISABLED: bool
    BASE_URL: str


CONFIG = Config(
    ENVIRONMENT=os.getenv("ENVIRONMENT", "development"),
    DEBUG=os.getenv("DEBUG", "True").lower() == "true",
    SECRET_KEY=os.getenv("SECRET_KEY", "your-secret-key-change-in-production"),
    CORS_ORIGINS=os.getenv("CORS_ORIGINS", "*").split(","),
    RATE_LIMIT_RATE=int(os.getenv("RATE_LIMIT_RATE", "60")),
    RATE_LIMIT_PER=int(os.getenv("RATE_LIMIT_PER", "60")),
    FIREBASE=FirebaseConfig(
        FIREBASE_API_KEY=os.getenv("FIREBASE_API_KEY", ""),
        FIREBASE_URL=os.getenv("FIREBASE_URL", "https://yoruichi-99389-default-rtdb.firebaseio.com/"),
        FIREBASE_CERT_FILE_PATH=os.getenv("FIREBASE_CERT_FILE_PATH", "firebase_client/firebase-cert.json"),
    ),
    ADMIN_USERNAME=os.getenv("ADMIN_USERNAME", "admin"),
    ADMIN_EMAIL=os.getenv("ADMIN_EMAIL", "admin@example.com"),
    ADMIN_PASSWORD=os.getenv("ADMIN_PASSWORD", "admin_password_for_development"),
    ADMIN_DISABLED=os.getenv("ADMIN_DISABLED", "False").lower() == "true",
    BASE_URL=os.getenv("BASE_URL", "http://localhost:8000"),
)

# Gmail configuration
GMAIL_SENDER_EMAIL = os.getenv("GMAIL_SENDER_EMAIL", "")
GMAIL_SENDER_SECRET = os.getenv("GMAIL_SENDER_SECRET", "")
