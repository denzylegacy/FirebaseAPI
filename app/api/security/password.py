# -*- coding: utf-8 -*-

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password to compare against
        
    Returns:
        True if the password matches the hash, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Generate a password hash
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    hashed = pwd_context.hash(password)
    print(f"Hashed result: {hashed}")
    return hashed 