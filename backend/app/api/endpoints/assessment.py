from typing import Any, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...api.deps import get_current_user
from ...models.user_management import User, StudentProfile, ParentStudentRelation
from ...models.assessments import Assessment, AssessmentResult, StudentAnswer, Question, QuestionType
from ...schemas.assessments import (
    AssessmentCreate, AssessmentResponse, AssessmentWithQuestions,
    AssessmentResultCreate, AssessmentResultResponse, AssessmentResultWithStudentAnswers,
    StudentAnswerCreate, StudentAnswerResponse
)

router = APIRouter()


@router.post("/create-worksheet", response_model=AssessmentResponse)
def create_worksheet(
    assessment_data: AssessmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create a new worksheet assessment.
    """
    # Only teachers can create assessments
    if current_user.user_type != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can create assessments"
        )
    
    # Create assessment
    assessment = Assessment(
        title=assessment_data.title,
        type="worksheet",  # Explicitly set to worksheet
        class_id=assessment_data.class_id,
        subject_id=assessment_data.subject_id,
        topic_id=assessment_data.topic_id,
        difficulty=assessment_data.difficulty,
        duration=assessment_data.duration,
        total_marks=assessment_data.total_marks,
        created_by=current_user.id
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    
    return assessment


@router.get("/", response_model=List[AssessmentResponse])
def get_assessments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    List all assessments based on user type.
    - Teachers see all assessments they created
    - Students see all assessments for their class
    - Parents see all assessments for their linked students' classes
    """
    if current_user.user_type == "teacher":
        # Teachers see all assessments they created
        assessments = db.query(Assessment).filter(
            Assessment.created_by == current_user.id
        ).all()
    elif current_user.user_type == "student":
        # Get student profile
        student_profile = db.query(StudentProfile).filter(
            StudentProfile.user_id == current_user.id
        ).first()
        
        if not student_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found"
            )
        
        # Find the class ID that matches the student's grade
        from ...models.academic_hierarchy import Class
        class_obj = db.query(Class).filter(
            Class.name == student_profile.normalized_grade
        ).first()
        
        if not class_obj:
            # If no class matches the grade, return empty list
            return []
        
        # Students see all assessments for their class
        assessments = db.query(Assessment).filter(
            Assessment.class_id == str(class_obj.id)
        ).all()
    elif current_user.user_type == "parent":
        # Get all student profiles linked to this parent
        from ...models.user_management import ParentStudentRelation
        student_profiles = (
            db.query(StudentProfile)
            .join(ParentStudentRelation)
            .filter(ParentStudentRelation.parent_id == current_user.id)
            .all()
        )
        
        if not student_profiles:
            return []
        
        # Get all class IDs for these students
        from ...models.academic_hierarchy import Class
        class_ids = []
        
        for sp in student_profiles:
            class_obj = db.query(Class).filter(
                Class.name == sp.normalized_grade
            ).first()
            if class_obj:
                class_ids.append(str(class_obj.id))
        
        if not class_ids:
            return []
        
        # Parents see all assessments for their linked students' classes
        assessments = db.query(Assessment).filter(
            Assessment.class_id.in_(class_ids)
        ).all()
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized user type"
        )
    
    return assessments


@router.get("/{id}", response_model=AssessmentWithQuestions)
def get_assessment(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get assessment details with questions.
    """
    # Get assessment
    assessment = db.query(Assessment).filter(Assessment.id == id).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    # Check if user has access to this assessment
    if current_user.user_type == "teacher":
        # Teachers can only view assessments they created
        if assessment.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view assessments you created"
            )
    elif current_user.user_type == "student":
        # Get student profile
        student_profile = db.query(StudentProfile).filter(
            StudentProfile.user_id == current_user.id
        ).first()
        
        if not student_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found"
            )
        
        # Find the class ID that matches the student's grade
        from ...models.academic_hierarchy import Class
        class_obj = db.query(Class).filter(
            Class.name == student_profile.normalized_grade
        ).first()
        
        if not class_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class not found for student's grade"
            )
        
        # Students can only view assessments for their class
        if assessment.class_id != str(class_obj.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view assessments for your class"
            )
    elif current_user.user_type == "parent":
        # Parents can only view assessments for their linked students' classes
        from ...models.user_management import ParentStudentRelation
        is_linked = db.query(ParentStudentRelation).filter(
            ParentStudentRelation.parent_id == current_user.id
        ).first()
        
        if not is_linked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view assessments for your linked students"
            )
        
        # Check if assessment is for any of the linked student's classes
        student_profiles = (
            db.query(StudentProfile)
            .join(ParentStudentRelation)
            .filter(ParentStudentRelation.parent_id == current_user.id)
            .all()
        )
        
        # Get all class IDs for these students
        from ...models.academic_hierarchy import Class
        class_ids = []
        
        for sp in student_profiles:
            class_obj = db.query(Class).filter(
                Class.name == sp.normalized_grade
            ).first()
            if class_obj:
                class_ids.append(str(class_obj.id))
        
        if not class_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No classes found for linked students"
            )
        
        if assessment.class_id not in class_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view assessments for your linked students' classes"
            )
    
    return assessment


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
    answers_data: dict,  # Changed to accept a dict with answers array
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Submit answers for grading and results.
    """
    try:
        print(f"Submitting quiz {id} with answers data: {answers_data}")
        
        # Extract answers from the request data
        answers = answers_data.get("answers", [])
        if not answers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No answers provided"
            )
        
        print(f"Submitting quiz {id} with {len(answers)} answers")
        
        # Get assessment
        from uuid import UUID
        try:
            assessment_uuid = UUID(id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid assessment ID format"
            )
            
        assessment = db.query(Assessment).filter(Assessment.id == assessment_uuid).first()
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found"
            )
        
        print(f"Found assessment: {assessment.title}")
        
        # Students or parents can submit quizzes
        if current_user.user_type not in ["student", "parent"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only students or parents can submit quizzes"
            )
        
        # Get student profile for the current user
        # For students, we use their own student profile
        # For parents, we need to find the student profile based on the user_id in the answers
        student_profile = None
        
        if current_user.user_type == "student":
            # Students can only submit for their own profile
            student_profile = db.query(StudentProfile).filter(
                StudentProfile.user_id == current_user.id
            ).first()
            
            if not student_profile:
                print(f"Student profile not found for user: {current_user.id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Student profile not found for current user"
                )
        elif current_user.user_type == "parent":
            # Parents can submit for their linked students
            # Get the user_id from the first answer
            user_id = None
            for answer in answers:
                current_user_id = answer.get("student_profile_id")  # This is actually the user_id
                if not current_user_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="User ID not provided in one or more answers"
                    )
                
                if user_id is None:
                    user_id = current_user_id
                elif user_id != current_user_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="All answers must have the same user ID"
                    )
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User ID not provided"
                )
            
            print(f"User ID from answers: {user_id}")
            
            # Convert string UUID to UUID object if needed
            from uuid import UUID
            try:
                user_uuid = UUID(user_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid user ID format"
                )
            
            # Check if this user is a student linked to the current parent
            from ...models.user_management import ParentStudentRelation
            is_linked = db.query(ParentStudentRelation).filter(
                ParentStudentRelation.parent_id == current_user.id,
                ParentStudentRelation.student_profile_id == user_uuid
            ).first()
            
            if not is_linked:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only submit quizzes for your linked students"
                )
            
            # Get the student profile for this user
            student_profile = db.query(StudentProfile).filter(
                StudentProfile.user_id == user_uuid
            ).first()
            
            if not student_profile:
                print(f"Student profile not found for user: {user_uuid}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Student profile not found for the specified user"
                )
        
        print(f"Found student profile: {student_profile.name}")
        
        print(f"Found student profile: {student_profile.name}")
        
        # Access control has already been checked above when retrieving the student profile
        
        # Check if there's already a result for this student and assessment
        existing_result = db.query(AssessmentResult).filter(
            AssessmentResult.assessment_id == assessment_uuid,
            AssessmentResult.student_profile_id == student_profile.id
        ).first()
        
        if existing_result:
            print(f"Updating existing assessment result: {existing_result.id}")
            # Update existing result instead of creating a new one
            assessment_result = existing_result
            assessment_result.total_score = 0  # Will be recalculated
            assessment_result.percentage = 0  # Will be recalculated
            assessment_result.completed_at = datetime.utcnow()
            
            # Delete existing student answers
            db.query(StudentAnswer).filter(
                StudentAnswer.assessment_result_id == assessment_result.id
            ).delete()
        else:
            print("Creating new assessment result")
            # Create new assessment result
            assessment_result = AssessmentResult(
                assessment_id=assessment_uuid,
                student_profile_id=student_profile.id,
                total_score=0,  # Will be calculated
                percentage=0,  # Will be calculated
                completed_at=datetime.utcnow()
            )
            db.add(assessment_result)
        
        db.commit()
        db.refresh(assessment_result)
        print(f"Assessment result created/updated: {assessment_result.id}")
        
        # Process answers
        total_score = 0
        total_possible = 0
        
        for i, answer_data in enumerate(answers):
            print(f"Processing answer {i+1}/{len(answers)}")
            print(f"Answer data: {answer_data}")
            
            # Get question
            question_id = answer_data.get("question_id")
            if not question_id:
                print(f"Question ID not found in answer data: {answer_data}")
                continue
            
            # Convert string UUID to UUID object if needed
            from uuid import UUID
            try:
                question_uuid = UUID(question_id)
            except ValueError:
                print(f"Invalid question ID format: {question_id}")
                continue
                
            question = db.query(Question).filter(Question.id == question_uuid).first()
            if not question:
                print(f"Question not found: {question_id}")
                continue
            
            # Verify question belongs to this assessment
            if str(question.assessment_id) != id:
                print(f"Question {question.id} does not belong to assessment {assessment.id}")
                continue
            
            total_possible += question.marks
            
            # Get the answer text
            answer_text = answer_data.get("answer", "")
            
            # Create student answer
            student_answer = StudentAnswer(
                assessment_result_id=assessment_result.id,
                question_id=question_uuid,
                answer=answer_text,
                score=0  # Will be calculated
            )
            
            # Grade the answer
            try:
                if question.type == QuestionType.MULTIPLE_CHOICE:
                    # For multiple choice, check if the answer matches the correct answer
                    if answer_text.strip().lower() == question.correct_answer.strip().lower():
                        student_answer.score = question.marks
                        total_score += question.marks
                        print(f"Correct answer for question {question.id}, score: {student_answer.score}")
                    else:
                        student_answer.score = 0
                        print(f"Incorrect answer for question {question.id}, score: {student_answer.score}")
                elif question.type == QuestionType.TRUE_FALSE:
                    # For true/false, check if the answer matches the correct answer
                    if answer_text.strip().lower() == question.correct_answer.strip().lower():
                        student_answer.score = question.marks
                        total_score += question.marks
                        print(f"Correct answer for question {question.id}, score: {student_answer.score}")
                    else:
                        student_answer.score = 0
                        print(f"Incorrect answer for question {question.id}, score: {student_answer.score}")
                else:
                    # For short answer and essay, we'll need manual grading or AI grading
                    # For now, give partial credit (50%)
                    student_answer.score = question.marks * 0.5
                    total_score += student_answer.score
                    print(f"Partial credit for question {question.id}, score: {student_answer.score}")
                
                db.add(student_answer)
                print(f"Added student answer for question {question.id}")
            except Exception as e:
                print(f"Error grading answer for question {question.id}: {str(e)}")
                raise e
        
        # Calculate percentage
        if total_possible > 0:
            assessment_result.percentage = (total_score / total_possible) * 100
        else:
            assessment_result.percentage = 0
            
        assessment_result.total_score = total_score
        
        print(f"Final score: {total_score}/{total_possible} ({assessment_result.percentage}%)")
        
        db.commit()
        db.refresh(assessment_result)
        
        print(f"Assessment result saved successfully: {assessment_result.id}")
        
        return assessment_result
    except Exception as e:
        import traceback
        print(f"Error submitting quiz: {str(e)}")
        print(f"Full traceback: {traceback.format_exc()}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit quiz: {str(e)}"
        )


@router.post("/submit-worksheet/{id}", response_model=AssessmentResultResponse)
def submit_worksheet(
    id: str,
    answers_data: dict,  # Changed to accept a dict with answers array
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Submit worksheet answers for grading and results.
    This is essentially the same as submitting a quiz.
    """
    return submit_quiz(id, answers_data, current_user, db)


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