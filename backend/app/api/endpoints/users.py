from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user_management import User, StudentProfile, StudentInterest, StudentAchievement, ParentStudentRelation
from ..schemas.user_management import (
    UserResponse, UserUpdate, StudentProfileResponse, 
    StudentProfileUpdate, StudentInterestCreate, StudentInterestResponse,
    StudentAchievementResponse
)

router = APIRouter()


@router.get("/profile", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get current user's profile data.
    """
    return current_user


@router.put("/profile", response_model=UserResponse)
def update_current_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update current user profile.
    """
    # Update user fields
    for field, value in user_data.dict(exclude_unset=True).items():
        if field == "password" and value:
            # Hash password if it's being updated
            from ..core.security import get_password_hash
            setattr(current_user, field, get_password_hash(value))
        else:
            setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.get("/students", response_model=List[StudentProfileResponse])
def get_linked_student_profiles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get all linked student profiles for a parent.
    """
    if current_user.user_type != "parent":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can access student profiles"
        )
    
    # Get all student profiles linked to this parent
    student_profiles = (
        db.query(StudentProfile)
        .join(ParentStudentRelation)
        .filter(ParentStudentRelation.parent_id == current_user.id)
        .all()
    )
    
    return student_profiles


@router.post("/students/verify-pin")
def verify_student_pin(
    student_profile_id: str,
    pin: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Verify student PIN for profile access.
    """
    # Get student profile
    student_profile = db.query(StudentProfile).filter(
        StudentProfile.id == student_profile_id
    ).first()
    
    if not student_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    # Verify PIN
    if student_profile.pin != pin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PIN"
        )
    
    # Check if parent is linked to this student
    if current_user.user_type == "parent":
        is_linked = db.query(ParentStudentRelation).filter(
            ParentStudentRelation.parent_id == current_user.id,
            ParentStudentRelation.student_profile_id == student_profile_id
        ).first()
        
        if not is_linked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not linked to this student"
            )
    
    return {"message": "PIN verified successfully", "student_profile_id": student_profile_id}


@router.put("/student-profiles/{id}/interests", response_model=List[StudentInterestResponse])
def update_student_interests(
    id: str,
    interests: List[StudentInterestCreate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Save/update student interests.
    """
    # Get student profile
    student_profile = db.query(StudentProfile).filter(
        StudentProfile.id == id
    ).first()
    
    if not student_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    # Check if user has access to this student profile
    if current_user.user_type == "parent":
        is_linked = db.query(ParentStudentRelation).filter(
            ParentStudentRelation.parent_id == current_user.id,
            ParentStudentRelation.student_profile_id == id
        ).first()
        
        if not is_linked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not linked to this student"
            )
    elif current_user.user_type == "student":
        if student_profile.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own interests"
            )
    
    # Delete existing interests
    db.query(StudentInterest).filter(
        StudentInterest.student_profile_id == id
    ).delete()
    
    # Add new interests
    for interest_data in interests:
        interest = StudentInterest(
            student_profile_id=id,
            interest_name=interest_data.interest_name
        )
        db.add(interest)
    
    db.commit()
    
    # Get updated interests
    updated_interests = db.query(StudentInterest).filter(
        StudentInterest.student_profile_id == id
    ).all()
    
    return updated_interests


@router.get("/student-profiles/{id}/achievements", response_model=List[StudentAchievementResponse])
def get_student_achievements(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Fetch list of student achievements.
    """
    # Get student profile
    student_profile = db.query(StudentProfile).filter(
        StudentProfile.id == id
    ).first()
    
    if not student_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    # Check if user has access to this student profile
    if current_user.user_type == "parent":
        is_linked = db.query(ParentStudentRelation).filter(
            ParentStudentRelation.parent_id == current_user.id,
            ParentStudentRelation.student_profile_id == id
        ).first()
        
        if not is_linked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not linked to this student"
            )
    elif current_user.user_type == "student":
        if student_profile.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own achievements"
            )
    
    # Get achievements
    achievements = db.query(StudentAchievement).filter(
        StudentAchievement.student_profile_id == id
    ).all()
    
    return achievements