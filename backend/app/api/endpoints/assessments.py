from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ...core.database import get_db
from ...api.deps import get_current_user
from ...models.user_management import User
from ...models.assessments import Assessment, Question, StudentAnswer

router = APIRouter()


class AnswerSubmission(BaseModel):
    question_id: str
    answer: str
    student_profile_id: str


class QuizSubmission(BaseModel):
    answers: List[AnswerSubmission]


@router.post("/submit-quiz/{assessment_id}")
async def submit_quiz_answers(
    assessment_id: str,
    submission: QuizSubmission,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Submit quiz answers and get results.
    """
    # Verify assessment exists
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    # Process each answer
    results = []
    for answer_data in submission.answers:
        # Find the question
        question = db.query(Question).filter(Question.id == answer_data.question_id).first()
        if not question:
            continue
        
        # Check if answer is correct
        is_correct = False
        if question.type in ["MULTIPLE_CHOICE", "TRUE_FALSE"]:
            # For multiple choice and true/false, compare directly
            if isinstance(question.correct_answer, list):
                is_correct = answer_data.answer in question.correct_answer
            else:
                is_correct = answer_data.answer == question.correct_answer
        else:
            # For short answer and essay, use a simple contains check
            # In a real implementation, you might use more sophisticated NLP
            if isinstance(question.correct_answer, str):
                is_correct = answer_data.answer.lower() in question.correct_answer.lower() or \
                            question.correct_answer.lower() in answer_data.answer.lower()
        
        # Save the student answer
        student_answer = StudentAnswer(
            assessment_id=assessment_id,
            question_id=answer_data.question_id,
            student_profile_id=answer_data.student_profile_id,
            answer=answer_data.answer,
            is_correct=is_correct
        )
        db.add(student_answer)
        
        # Add to results
        results.append({
            "question_id": answer_data.question_id,
            "is_correct": is_correct,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation
        })
    
    db.commit()
    
    # Calculate score
    correct_count = sum(1 for r in results if r["is_correct"])
    total_count = len(results)
    score_percentage = (correct_count / total_count) * 100 if total_count > 0 else 0
    
    return {
        "assessment_id": assessment_id,
        "score": {
            "correct": correct_count,
            "total": total_count,
            "percentage": score_percentage
        },
        "results": results
    }


@router.post("/submit-worksheet/{assessment_id}")
async def submit_worksheet_answers(
    assessment_id: str,
    submission: QuizSubmission,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Submit worksheet answers and get results.
    """
    # This is essentially the same as submitting a quiz
    # We can reuse the same logic
    return await submit_quiz_answers(assessment_id, submission, current_user, db)