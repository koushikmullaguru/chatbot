from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...api.deps import get_current_user
from ...models.user_management import User, StudentProfile, ParentStudentRelation
from ...models.assessments import Assessment, AssessmentResult, StudentAnswer, Question
from ...schemas.assessments import (
    AssessmentCreate, AssessmentResponse, AssessmentWithQuestions,
    AssessmentResultCreate, AssessmentResultResponse, AssessmentResultWithStudentAnswers,
    StudentAnswerCreate, StudentAnswerResponse
)

router = APIRouter()


@router.get("/", response_model=List[AssessmentResponse])
def get_assessments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    List all teacher-created assessments.
    """
    # Only teachers can view assessments they created
    if current_user.user_type != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can view assessments"
        )
    
    assessments = db.query(Assessment).filter(
        Assessment.created_by == current_user.id
    ).all()
    
    return assessments


@router.post("/start-quiz/{id}")
def start_quiz(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Log the start of a quiz attempt.
    """
    # Get assessment
    assessment = db.query(Assessment).filter(Assessment.id == id).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    # Students or parents can start quizzes
    if current_user.user_type not in ["student", "parent"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students or parents can start quizzes"
        )
    
    # TODO: Create an assessment result record
    # For now, just return a success message
    return {
        "message": "Quiz started successfully",
        "assessment_id": id,
        "status": "in_progress"
    }


@router.post("/submit-quiz/{id}", response_model=AssessmentResultResponse)
def submit_quiz(
    id: str,
    answers: List[StudentAnswerCreate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Submit answers for grading and results.
    """
    # Get assessment
    assessment = db.query(Assessment).filter(Assessment.id == id).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    # Students or parents can submit quizzes
    if current_user.user_type not in ["student", "parent"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students or parents can submit quizzes"
        )
    
    # TODO: Verify student profile ID is valid and accessible by current user
    
    # Create assessment result
    assessment_result = AssessmentResult(
        assessment_id=id,
        student_profile_id=answers[0].student_profile_id if answers else "",
        total_score=0,  # Will be calculated
        percentage=0,  # Will be calculated
    )
    db.add(assessment_result)
    db.commit()
    db.refresh(assessment_result)
    
    # Process answers
    total_score = 0
    total_possible = 0
    
    for answer_data in answers:
        # Get question
        question = db.query(Question).filter(Question.id == answer_data.question_id).first()
        if not question:
            continue
        
        total_possible += question.marks
        
        # Create student answer
        student_answer = StudentAnswer(
            assessment_result_id=assessment_result.id,
            question_id=answer_data.question_id,
            answer=answer_data.answer,
            score=0  # Will be calculated
        )
        
        # TODO: Grade the answer
        # For now, assume all answers are correct
        student_answer.score = question.marks
        total_score += question.marks
        
        db.add(student_answer)
    
    # Calculate percentage
    if total_possible > 0:
        assessment_result.percentage = (total_score / total_possible) * 100
    else:
        assessment_result.percentage = 0
    
    assessment_result.total_score = total_score
    
    db.commit()
    db.refresh(assessment_result)
    
    return assessment_result


@router.get("/quiz-results/{id}", response_model=AssessmentResultWithStudentAnswers)
def get_quiz_result(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Fetch detailed quiz result.
    """
    # Get assessment result
    assessment_result = db.query(AssessmentResult).filter(
        AssessmentResult.id == id
    ).first()
    
    if not assessment_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz result not found"
        )
    
    # Check if user has access to this result
    if current_user.user_type == "student":
        # Students can only view their own results
        student_profile = db.query(StudentProfile).filter(
            StudentProfile.user_id == current_user.id
        ).first()
        
        if not student_profile or assessment_result.student_profile_id != student_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own quiz results"
            )
    elif current_user.user_type == "parent":
        # Parents can only view results of their linked students
        is_linked = db.query(ParentStudentRelation).filter(
            ParentStudentRelation.parent_id == current_user.id,
            ParentStudentRelation.student_profile_id == assessment_result.student_profile_id
        ).first()
        
        if not is_linked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view quiz results of your linked students"
            )
    elif current_user.user_type == "teacher":
        # Teachers can only view results of assessments they created
        assessment = db.query(Assessment).filter(
            Assessment.id == assessment_result.assessment_id
        ).first()
        
        if not assessment or assessment.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view results of assessments you created"
            )
    
    return assessment_result


@router.get("/student-quiz-results", response_model=List[AssessmentResultResponse])
def get_student_quiz_results(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    List all results for a student.
    """
    if current_user.user_type == "student":
        # Get student profile
        student_profile = db.query(StudentProfile).filter(
            StudentProfile.user_id == current_user.id
        ).first()
        
        if not student_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found"
            )
        
        # Get all results for this student
        results = db.query(AssessmentResult).filter(
            AssessmentResult.student_profile_id == student_profile.id
        ).all()
        
        return results
    elif current_user.user_type == "parent":
        # Get all student profiles linked to this parent
        student_profiles = (
            db.query(StudentProfile)
            .join(ParentStudentRelation)
            .filter(ParentStudentRelation.parent_id == current_user.id)
            .all()
        )
        
        if not student_profiles:
            return []
        
        # Get all results for these students
        student_profile_ids = [sp.id for sp in student_profiles]
        results = db.query(AssessmentResult).filter(
            AssessmentResult.student_profile_id.in_(student_profile_ids)
        ).all()
        
        return results
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students and parents can view quiz results"
        )