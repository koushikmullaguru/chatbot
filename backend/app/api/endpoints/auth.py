from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.config import settings
from ...core.database import get_db
from ...core.security import get_password_hash, verify_password
from ...models.user_management import User
from ...schemas.user_management import (
    UserCreate, UserResponse, UserLogin, Token
)
from ..deps import get_current_user

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
    Login with email/password; returns a simple token.
    """
    # Authenticate user
    user = db.query(User).filter(User.email == user_credentials.email).first()
    if not user or not verify_password(user_credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Return the user ID as the token (in a real app, you would generate a proper token)
    return {"access_token": str(user.id), "token_type": "bearer"}


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)) -> Any:
    """
    Simple logout endpoint.
    """
    return {"message": "Successfully logged out"}