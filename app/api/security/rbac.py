# -*- coding: utf-8 -*-

from fastapi import Depends, HTTPException, status
from app.api.models.schemas import User
from app.api.security.jwt import get_current_active_user
from app.settings import log


async def get_current_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Dependency to check if the current user is an admin
    
    Args:
        current_user: The authenticated user
        
    Returns:
        The user if they are an admin
        
    Raises:
        HTTPException: If the user is not an admin
    """
    if not getattr(current_user, "is_admin", False):
        await log.async_warning(f"Non-admin user {current_user.username} attempted to access admin-only endpoint")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized. Admin privileges required."
        )
    return current_user 