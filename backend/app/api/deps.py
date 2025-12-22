"""
Dependencies for API endpoints
"""
from fastapi import Security, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from uuid import UUID

from ..core.database import get_db
from ..core.security import verify_token, verify_user_session
from ..models.user_management import User
from ..models.system import UserSession

# Security scheme
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current user from the Bearer token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verify token
    token = credentials.credentials
    user_id = verify_token(token)
    if user_id is None:
        print(f"Token verification failed for token: {token[:10]}...")
        raise credentials_exception
    
    # Get user from database
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        print(f"Invalid UUID format: {user_id}")
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_uuid).first()
    if user is None:
        print(f"User not found with ID: {user_uuid}")
        raise credentials_exception
    
    # Verify user session
    if not verify_user_session(db, user_uuid, token):
        print(f"User session verification failed for user: {user_uuid}")
        raise credentials_exception
    
    print(f"Successfully authenticated user: {user.id}")
    return user


# Re-export the get_current_user function for use in other endpoints
__all__ = ["get_current_user"]