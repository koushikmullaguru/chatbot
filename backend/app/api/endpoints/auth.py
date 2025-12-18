from datetime import timedelta, datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..core import security
from ..core.config import settings
from ..core.database import get_db
from ..models.user_management import User, OtpVerification, UserSession
from ..schemas.user_management import (
    UserCreate, UserResponse, UserLogin, Token, 
    OtpRequest, OtpVerify, TokenData
)
from ..schemas.system import OtpVerificationResponse, UserSessionResponse

router = APIRouter()


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
    
    # Hash password
    hashed_password = security.get_password_hash(user_data.password)
    
    # Create user
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
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> Any:
    """
    Login with email/password; returns JWT.
    """
    # Authenticate user
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    # Create user session
    session = UserSession(
        user_id=user.id,
        token=access_token,
        expires_at=datetime.utcnow() + access_token_expires
    )
    db.add(session)
    db.commit()
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/send-otp")
def send_otp(otp_data: OtpRequest, db: Session = Depends(get_db)) -> Any:
    """
    Send parent login code to email.
    """
    # Check if user exists and is a parent
    user = db.query(User).filter(User.email == otp_data.email).first()
    if not user or user.user_type != "parent":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent user not found"
        )
    
    # Generate OTP
    otp = security.generate_otp()
    
    # Save OTP
    otp_verification = OtpVerification(
        email=otp_data.email,
        otp=otp
    )
    db.add(otp_verification)
    db.commit()
    
    # In a real application, you would send the OTP via email
    # For now, we'll just return a success message
    return {"message": "OTP sent successfully"}


@router.post("/verify-otp", response_model=Token)
def verify_otp(otp_data: OtpVerify, db: Session = Depends(get_db)) -> Any:
    """
    Verify OTP and return access token.
    """
    # Get OTP verification record
    otp_verification = db.query(OtpVerification).filter(
        OtpVerification.email == otp_data.email,
        OtpVerification.otp == otp_data.otp,
        OtpVerification.verified == False
    ).first()
    
    if not otp_verification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP"
        )
    
    # Check if OTP is expired
    if otp_verification.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP expired"
        )
    
    # Get user
    user = db.query(User).filter(User.email == otp_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Mark OTP as verified
    otp_verification.verified = True
    db.commit()
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    # Create user session
    session = UserSession(
        user_id=user.id,
        token=access_token,
        expires_at=datetime.utcnow() + access_token_expires
    )
    db.add(session)
    db.commit()
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout(token_data: TokenData, db: Session = Depends(get_db)) -> Any:
    """
    Invalidate session/token.
    """
    # Get user session
    session = db.query(UserSession).filter(
        UserSession.user_id == token_data.user_id,
        UserSession.token == token_data.token
    ).first()
    
    if session:
        # Delete session
        db.delete(session)
        db.commit()
    
    return {"message": "Successfully logged out"}