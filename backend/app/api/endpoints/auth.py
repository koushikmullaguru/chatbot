from datetime import datetime, timedelta
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from uuid import UUID

from ...core.config import settings
from ...core.database import get_db
from ...core.security import (
    get_password_hash, verify_password, create_access_token,
    generate_otp, create_user_session, revoke_user_session, verify_token
)
from ...models.system import UserSession
from ...models.user_management import User
from ...schemas.user_management import (
    UserCreate, UserResponse, UserLogin, Token, OtpRequest, OtpVerify
)
from ..deps import get_current_user, security

router = APIRouter()

# In-memory OTP storage (in production, use Redis or database)
otp_storage = {}


@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)) -> Any:
    """
    Register new user (Teacher, Parent, Student).
    """
    # Check if user already exists
    user = db.query(User).filter(User.email == user_data.email).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user with password hashing
    hashed_password = get_password_hash(user_data.password)
    user = User(
        name=user_data.name,
        email=user_data.email,
        password=hashed_password,
        user_type=user_data.user_type,
        grade=user_data.grade,
        subject=user_data.subject,
        teacher_role=user_data.teacher_role,
        teacher_subject=user_data.teacher_subject,
        teacher_class=user_data.teacher_class
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@router.post("/login", response_model=Token)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)) -> Any:
    """
    Login with email/password; returns a JWT token.
    """
    # Authenticate user
    user = db.query(User).filter(User.email == user_credentials.email).first()
    if not user or not verify_password(user_credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id), expires_delta=access_token_expires
    )
    
    # Create user session
    create_user_session(db, user.id, access_token)
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/request-otp")
def request_otp(otp_request: OtpRequest, db: Session = Depends(get_db)) -> Any:
    """
    Request OTP for parent login.
    """
    # Check if user exists and is a parent
    user = db.query(User).filter(User.email == otp_request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.user_type.value != "parent":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP login is only available for parents"
        )
    
    # Generate OTP (in production, send via email/SMS)
    otp = generate_otp()
    
    # Store OTP with expiration (5 minutes)
    expiration_time = datetime.utcnow() + timedelta(minutes=5)
    otp_storage[otp_request.email] = {
        "otp": otp,
        "expires_at": expiration_time
    }
    
    # In production, send OTP via email/SMS here
    # For demo purposes, we'll just return the OTP
    return {
        "message": "OTP sent successfully",
        "otp": otp  # Remove in production
    }


@router.post("/verify-otp", response_model=Token)
def verify_otp(otp_verify: OtpVerify, db: Session = Depends(get_db)) -> Any:
    """
    Verify OTP and return JWT token.
    """
    # Check if OTP exists and is valid
    if otp_verify.email not in otp_storage:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP not requested or expired"
        )
    
    stored_otp = otp_storage[otp_verify.email]
    
    # Check if OTP is expired
    if datetime.utcnow() > stored_otp["expires_at"]:
        # Remove expired OTP
        del otp_storage[otp_verify.email]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP expired"
        )
    
    # Verify OTP
    if stored_otp["otp"] != otp_verify.otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP"
        )
    
    # Get user
    user = db.query(User).filter(User.email == otp_verify.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Remove used OTP
    del otp_storage[otp_verify.email]
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id), expires_delta=access_token_expires
    )
    
    # Create user session
    create_user_session(db, user.id, access_token)
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/refresh", response_model=Token)
def refresh_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
) -> Any:
    """
    Refresh JWT token.
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
    
    # Check if user has any active session (even if current token is expired)
    active_session = db.query(UserSession).filter(
        UserSession.user_id == user_uuid,
        UserSession.is_active == True
    ).first()
    
    if not active_session:
        raise credentials_exception
    
    # Create new access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id), expires_delta=access_token_expires
    )
    
    # Create new user session and revoke old ones
    create_user_session(db, user.id, access_token)
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
) -> Any:
    """
    Logout endpoint that invalidates the user session.
    """
    token = credentials.credentials
    
    # Try to verify token and get user
    try:
        user_id = verify_token(token)
        if user_id:
            try:
                user_uuid = UUID(user_id)
                user = db.query(User).filter(User.id == user_uuid).first()
                if user:
                    # Revoke the user session
                    revoke_user_session(db, user.id, token)
            except ValueError:
                pass  # Invalid UUID, continue with generic response
    except Exception:
        pass  # Token verification failed, continue with generic response
    
    # Always return success response for security reasons
    # This prevents attackers from knowing if a token was valid or not
    return {"message": "Successfully logged out"}