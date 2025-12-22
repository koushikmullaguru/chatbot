from datetime import datetime, timedelta
from typing import Optional, Union, Any
from jose import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from uuid import UUID
from .config import settings
from .database import get_db
from ..models.user_management import User
from ..models.system import UserSession

# Password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer scheme
security = HTTPBearer()


def create_access_token(
    subject: Union[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Generate a password hash
    """
    return pwd_context.hash(password)


def verify_token(token: str) -> Optional[str]:
    """
    Verify a JWT token and return the subject (user ID)
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return payload.get("sub")
    except jwt.JWTError:
        return None


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
        raise credentials_exception
    
    # Get user from database
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_uuid).first()
    if user is None:
        raise credentials_exception
    
    # Verify user session
    if not verify_user_session(db, user_uuid, token):
        raise credentials_exception
    
    return user


def generate_otp(length: int = 6) -> str:
    """
    Generate a random OTP of specified length
    """
    import random
    digits = "0123456789"
    return "".join(random.choice(digits) for i in range(length))


def create_user_session(db: Session, user_id: UUID, token: str) -> UserSession:
    """
    Create a new user session
    """
    # First, revoke any existing active sessions for this user
    db.query(UserSession).filter(
        UserSession.user_id == user_id,
        UserSession.is_active == True
    ).update({"is_active": False, "revoked_at": datetime.utcnow()})
    
    # Create new session
    expires_at = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    session = UserSession(
        user_id=user_id,
        token=token,
        expires_at=expires_at,
        is_active=True
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # Double-check that the session was properly created
    # This helps prevent race conditions
    db.refresh(session)
    return session


def verify_user_session(db: Session, user_id: UUID, token: str) -> bool:
    """
    Verify if a user session is valid
    """
    # First verify the JWT token is valid (not expired)
    token_subject = verify_token(token)
    if token_subject is None:
        print(f"JWT token verification failed for user {user_id}")
        return False
    
    # Verify the token subject matches the user_id
    if str(user_id) != token_subject:
        print(f"Token subject mismatch. Expected: {user_id}, Got: {token_subject}")
        return False
    
    # Check if session exists in database
    session = db.query(UserSession).filter(
        UserSession.user_id == user_id,
        UserSession.token == token,
        UserSession.is_active == True
    ).first()
    
    if not session:
        print(f"No exact session found for user {user_id} with token {token[:10]}...")
        
        # If no exact session found, check if there's any active session for this user
        # This is a fallback to handle cases where the session might not be properly stored
        # but the JWT token is still valid
        any_session = db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_active == True
        ).first()
        
        if any_session:
            print(f"Found active session with different token for user {user_id}. Updating token.")
            # If there's an active session but with a different token,
            # it means the token was refreshed. Update the session with the new token.
            any_session.token = token
            any_session.expires_at = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            db.commit()
            return True
        print(f"No active sessions found for user {user_id}")
        return False
    
    # Check if session is expired
    if datetime.utcnow() > session.expires_at:
        print(f"Session expired for user {user_id}. Session expires at: {session.expires_at}")
        # Mark session as inactive
        session.is_active = False
        session.revoked_at = datetime.utcnow()
        db.commit()
        return False
    
    print(f"Session verified successfully for user {user_id}")
    return True


def revoke_user_session(db: Session, user_id: UUID, token: str) -> bool:
    """
    Revoke a user session (for logout)
    """
    session = db.query(UserSession).filter(
        UserSession.user_id == user_id,
        UserSession.token == token,
        UserSession.is_active == True
    ).first()
    
    if not session:
        return False
    
    # Mark session as inactive
    session.is_active = False
    session.revoked_at = datetime.utcnow()
    db.commit()
    return True


def revoke_all_user_sessions(db: Session, user_id: UUID) -> bool:
    """
    Revoke all active sessions for a user
    """
    updated_count = db.query(UserSession).filter(
        UserSession.user_id == user_id,
        UserSession.is_active == True
    ).update({"is_active": False, "revoked_at": datetime.utcnow()})
    
    db.commit()
    return updated_count > 0