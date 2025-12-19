from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.security import get_password_hash
from ...api.deps import get_current_user
from ...models.user_management import User, StudentProfile, StudentInterest, StudentAchievement, ParentStudentRelation
from ...models.planner_performance import ReportCard, SubjectGrade
from ...schemas.user_management import (
    UserResponse, UserUpdate, StudentProfileResponse,
    StudentProfileCreate, StudentProfileUpdate, StudentInterestCreate, StudentInterestResponse,
    StudentAchievementCreate, StudentAchievementResponse, ParentStudentRelationCreate, ParentStudentRelationResponse
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
            hashed_password = get_password_hash(value)
            setattr(current_user, field, hashed_password)
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
    try:
        # Convert string ID to UUID if needed
        from uuid import UUID
        profile_id = UUID(student_profile_id) if isinstance(student_profile_id, str) else student_profile_id
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid student profile ID format"
        )
    
    # Get student profile
    student_profile = db.query(StudentProfile).filter(
        StudentProfile.id == profile_id
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
            ParentStudentRelation.student_profile_id == profile_id
        ).first()
        
        if not is_linked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not linked to this student"
            )
    
    return {"message": "PIN verified successfully", "student_profile_id": str(profile_id)}


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
    try:
        # Convert string ID to UUID if needed
        from uuid import UUID
        student_profile_id = UUID(id) if isinstance(id, str) else id
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid student profile ID format"
        )
    
    # Get student profile
    student_profile = db.query(StudentProfile).filter(
        StudentProfile.id == student_profile_id
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
        StudentInterest.student_profile_id == student_profile_id
    ).delete()
    
    # Add new interests
    for interest_data in interests:
        interest = StudentInterest(
            student_profile_id=student_profile_id,
            interest_name=interest_data.interest_name
        )
        db.add(interest)
    
    db.commit()
    
    # Get updated interests
    updated_interests = db.query(StudentInterest).filter(
        StudentInterest.student_profile_id == student_profile_id
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
    try:
        # Convert string ID to UUID if needed
        from uuid import UUID
        student_profile_id = UUID(id) if isinstance(id, str) else id
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid student profile ID format"
        )
    
    # Get student profile
    student_profile = db.query(StudentProfile).filter(
        StudentProfile.id == student_profile_id
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
            ParentStudentRelation.student_profile_id == student_profile_id
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
        StudentAchievement.student_profile_id == student_profile_id
    ).all()
    
    return achievements


@router.post("/student-profiles", response_model=StudentProfileResponse)
def create_student_profile(
    profile_data: StudentProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create a new student profile.
    """
    # Verify the user exists
    user = db.query(User).filter(User.id == profile_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Create student profile
    student_profile = StudentProfile(
        user_id=profile_data.user_id,
        name=profile_data.name,
        grade=profile_data.grade,
        avatar=profile_data.avatar,
        pin=profile_data.pin,
        roll_number=profile_data.roll_number,
        date_of_birth=profile_data.date_of_birth,
        blood_group=profile_data.blood_group,
        admission_date=profile_data.admission_date,
        email=profile_data.email,
        phone=profile_data.phone,
        address=profile_data.address,
        parent_name=profile_data.parent_name,
        parent_email=profile_data.parent_email,
        parent_phone=profile_data.parent_phone
    )
    db.add(student_profile)
    db.commit()
    db.refresh(student_profile)
    
    return student_profile


@router.get("/student-profiles/{id}", response_model=StudentProfileResponse)
def get_student_profile(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get student profile details.
    """
    try:
        # Convert string ID to UUID if needed
        from uuid import UUID
        student_profile_id = UUID(id) if isinstance(id, str) else id
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid student profile ID format"
        )
    
    # Get student profile
    student_profile = db.query(StudentProfile).filter(
        StudentProfile.id == student_profile_id
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
            ParentStudentRelation.student_profile_id == student_profile_id
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
                detail="You can only view your own profile"
            )
    
    return student_profile


@router.put("/student-profiles/{id}", response_model=StudentProfileResponse)
def update_student_profile(
    id: str,
    profile_data: StudentProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update student profile.
    """
    try:
        # Convert string ID to UUID if needed
        from uuid import UUID
        student_profile_id = UUID(id) if isinstance(id, str) else id
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid student profile ID format"
        )
    
    # Get student profile
    student_profile = db.query(StudentProfile).filter(
        StudentProfile.id == student_profile_id
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
            ParentStudentRelation.student_profile_id == student_profile_id
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
                detail="You can only update your own profile"
            )
    
    # Update student profile fields
    for field, value in profile_data.dict(exclude_unset=True).items():
        setattr(student_profile, field, value)
    
    db.commit()
    db.refresh(student_profile)
    
    return student_profile


@router.get("/student-profiles/{id}/interests", response_model=List[StudentInterestResponse])
def get_student_interests(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get student interests.
    """
    try:
        # Convert string ID to UUID if needed
        from uuid import UUID
        student_profile_id = UUID(id) if isinstance(id, str) else id
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid student profile ID format"
        )
    
    # Get student profile
    student_profile = db.query(StudentProfile).filter(
        StudentProfile.id == student_profile_id
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
            ParentStudentRelation.student_profile_id == student_profile_id
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
                detail="You can only view your own interests"
            )
    
    # Get interests
    interests = db.query(StudentInterest).filter(
        StudentInterest.student_profile_id == student_profile_id
    ).all()
    
    return interests


@router.post("/student-profiles/{id}/achievements", response_model=StudentAchievementResponse)
def add_student_achievement(
    id: str,
    achievement_data: StudentAchievementCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Add a new achievement for a student.
    """
    try:
        # Convert string ID to UUID if needed
        from uuid import UUID
        student_profile_id = UUID(id) if isinstance(id, str) else id
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid student profile ID format"
        )
    
    # Get student profile
    student_profile = db.query(StudentProfile).filter(
        StudentProfile.id == student_profile_id
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
            ParentStudentRelation.student_profile_id == student_profile_id
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
                detail="You can only add achievements to your own profile"
            )
    
    # Create achievement
    achievement = StudentAchievement(
        student_profile_id=student_profile_id,
        title=achievement_data.title,
        date=achievement_data.date,
        icon=achievement_data.icon
    )
    db.add(achievement)
    db.commit()
    db.refresh(achievement)
    
    return achievement


@router.put("/student-profiles/{id}/achievements/{achievement_id}", response_model=StudentAchievementResponse)
def update_student_achievement(
    id: str,
    achievement_id: str,
    achievement_data: StudentAchievementCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update an existing achievement for a student.
    """
    try:
        # Convert string ID to UUID if needed
        from uuid import UUID
        student_profile_id = UUID(id) if isinstance(id, str) else id
        achievement_uuid = UUID(achievement_id) if isinstance(achievement_id, str) else achievement_id
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
        )
    
    # Get student profile
    student_profile = db.query(StudentProfile).filter(
        StudentProfile.id == student_profile_id
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
            ParentStudentRelation.student_profile_id == student_profile_id
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
                detail="You can only update achievements on your own profile"
            )
    
    # Get achievement
    achievement = db.query(StudentAchievement).filter(
        StudentAchievement.id == achievement_uuid,
        StudentAchievement.student_profile_id == student_profile_id
    ).first()
    
    if not achievement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Achievement not found"
        )
    
    # Update achievement
    for field, value in achievement_data.dict(exclude_unset=True).items():
        setattr(achievement, field, value)
    
    db.commit()
    db.refresh(achievement)
    
    return achievement


@router.delete("/student-profiles/{id}/achievements/{achievement_id}")
def delete_student_achievement(
    id: str,
    achievement_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Delete an achievement for a student.
    """
    try:
        # Convert string ID to UUID if needed
        from uuid import UUID
        student_profile_id = UUID(id) if isinstance(id, str) else id
        achievement_uuid = UUID(achievement_id) if isinstance(achievement_id, str) else achievement_id
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
        )
    
    # Get student profile
    student_profile = db.query(StudentProfile).filter(
        StudentProfile.id == student_profile_id
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
            ParentStudentRelation.student_profile_id == student_profile_id
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
                detail="You can only delete achievements from your own profile"
            )
    
    # Get achievement
    achievement = db.query(StudentAchievement).filter(
        StudentAchievement.id == achievement_uuid,
        StudentAchievement.student_profile_id == student_profile_id
    ).first()
    
    if not achievement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Achievement not found"
        )
    
    # Delete achievement
    db.delete(achievement)
    db.commit()
    
    return {"message": "Achievement deleted successfully"}


@router.get("/student-profiles/{id}/report-cards")
def get_student_report_cards(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get student report cards.
    """
    try:
        # Convert string ID to UUID if needed
        from uuid import UUID
        student_profile_id = UUID(id) if isinstance(id, str) else id
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid student profile ID format"
        )
    
    # Get student profile
    student_profile = db.query(StudentProfile).filter(
        StudentProfile.id == student_profile_id
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
            ParentStudentRelation.student_profile_id == student_profile_id
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
                detail="You can only view your own report cards"
            )
    
    # Get report cards with subject grades
    report_cards_with_grades = []
    report_cards = db.query(ReportCard).filter(
        ReportCard.student_profile_id == student_profile_id
    ).all()
    
    for report_card in report_cards:
        subject_grades = db.query(SubjectGrade).filter(
            SubjectGrade.report_card_id == report_card.id
        ).all()
        
        report_card_with_grades = {
            "id": str(report_card.id),
            "student_profile_id": str(report_card.student_profile_id),
            "term": report_card.term,
            "year": report_card.year,
            "percentage": report_card.percentage,
            "rank": report_card.rank,
            "subject_grades": [
                {
                    "id": str(grade.id),
                    "subject": grade.subject,
                    "grade": grade.grade,
                    "marks": grade.marks,
                    "out_of": grade.out_of,
                    "percentage": grade.percentage
                }
                for grade in subject_grades
            ]
        }
        report_cards_with_grades.append(report_card_with_grades)
    
    return report_cards_with_grades


@router.post("/parent-student-relations", response_model=ParentStudentRelationResponse)
def create_parent_student_relation(
    relation_data: ParentStudentRelationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Link a parent to a student profile.
    """
    # Verify the current user is a parent
    if current_user.user_type != "parent":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can create student relations"
        )
    
    # Verify the student profile exists
    student_profile = db.query(StudentProfile).filter(
        StudentProfile.id == relation_data.student_profile_id
    ).first()
    
    if not student_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    # Check if relation already exists
    existing_relation = db.query(ParentStudentRelation).filter(
        ParentStudentRelation.parent_id == current_user.id,
        ParentStudentRelation.student_profile_id == relation_data.student_profile_id
    ).first()
    
    if existing_relation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Relation already exists"
        )
    
    # Create the relation
    relation = ParentStudentRelation(
        parent_id=current_user.id,
        student_profile_id=relation_data.student_profile_id
    )
    db.add(relation)
    db.commit()
    db.refresh(relation)
    
    return relation


@router.delete("/parent-student-relations/{relation_id}")
def delete_parent_student_relation(
    relation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Remove the link between a parent and student.
    """
    try:
        # Convert string ID to UUID if needed
        from uuid import UUID
        relation_uuid = UUID(relation_id) if isinstance(relation_id, str) else relation_id
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid relation ID format"
        )
    
    # Verify the current user is a parent
    if current_user.user_type != "parent":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can delete student relations"
        )
    
    # Get the relation
    relation = db.query(ParentStudentRelation).filter(
        ParentStudentRelation.id == relation_uuid,
        ParentStudentRelation.parent_id == current_user.id
    ).first()
    
    if not relation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Relation not found"
        )
    
    # Delete the relation
    db.delete(relation)
    db.commit()
    
    return {"message": "Relation deleted successfully"}