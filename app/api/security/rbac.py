# -*- coding: utf-8 -*-

from fastapi import Depends, HTTPException, status
from app.api.models.schemas import User
from app.api.security.jwt import get_current_active_user
from app.settings import log


async def get_current_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Get current user and verify admin privileges
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User if admin, raises exception otherwise
        
    Raises:
        HTTPException: If user is not an admin
    """
    await log.async_info(f"Checking admin privileges for user: {current_user.email}")
    await log.async_info(f"User admin status: {current_user.is_admin}")
    
    if not current_user.is_admin:
        await log.async_warning(f"Non-admin user {current_user.email} attempted to access admin-only endpoint")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin privileges required."
        )
    
    await log.async_info(f"Admin access granted for user: {current_user.email}")
    return current_user 