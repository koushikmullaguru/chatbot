from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ...core.database import get_db
from ...api.deps import get_current_user
from ...core.ai_service import ai_service
from ...models.user_management import User
from ...models.academic_hierarchy import Class, Subject, Chapter, Topic

router = APIRouter()


class QuizGenerateRequest(BaseModel):
    class_id: str
    subject_id: str
    chapter_id: str
    difficulty: str = "medium"
    num_questions: int = 10
    question_types: List[str] = ["multiple-choice"]
    duration: int = 30  # Default duration of 30 minutes


class ExamGenerateRequest(BaseModel):
    class_id: str
    subject_id: str
    chapter_ids: List[str]
    duration: int
    total_marks: int
    sections: List[Dict[str, Any]]


class RevisionGenerateRequest(BaseModel):
    subject_id: str
    topic_ids: List[str]
    revision_type: str = "notes"


class HomeworkGenerateRequest(BaseModel):
    class_id: str
    subject_id: str
    topic_id: str
    difficulty: str = "medium"
    num_questions: int = 5


class ContentGenerateRequest(BaseModel):
    class_id: str
    subject_id: str
    topic_id: str
    content_type: str = "notes"
    additional_info: Dict[str, Any] = {}


@router.post("/quiz")
async def generate_quiz(
    request: QuizGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    AI generates a quiz/worksheet and stores it in the database.
    """
    # Verify class exists
    class_obj = db.query(Class).filter(Class.id == request.class_id).first()
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    # Verify subject exists
    subject = db.query(Subject).filter(Subject.id == request.subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Verify chapter exists
    chapter = db.query(Chapter).filter(Chapter.id == request.chapter_id).first()
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found"
        )
    
    # Generate quiz using AI service
    quiz_result = await ai_service.generate_quiz(
        subject=subject.name,
        topic=chapter.name,
        difficulty=request.difficulty,
        num_questions=request.num_questions,
        question_types=request.question_types,
        duration=request.duration
    )
    
    # Check for errors
    if "error" in quiz_result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate quiz: {quiz_result['error']}"
        )
    
    # Extract the questions from the AI response
    try:
        # Get the content from the first choice
        content = quiz_result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Log the raw content for debugging
        print(f"Raw AI response content: {content}")
        
        # Extract JSON from the content (it might be wrapped in ```json\n```)
        import re
        json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
        if json_match:
            json_content = json_match.group(1)
            print(f"Extracted JSON content: {json_content}")
        else:
            # If no markdown formatting, try to parse the entire content as JSON
            json_content = content
            print(f"No JSON markdown found, using entire content: {json_content}")
        
        # Parse the JSON to get the questions
        import json
        questions_data = json.loads(json_content)
        questions = questions_data.get("questions", [])
        
        # Log the parsed questions for debugging
        print(f"Parsed questions: {questions}")
        
        # Create assessment in database
        from ...models.assessments import Assessment, Question, AssessmentType, QuestionType
        
        assessment = Assessment(
            title=f"{subject.name} - {chapter.name} Quiz",
            type=AssessmentType.QUIZ,
            class_id=request.class_id,
            subject_id=request.subject_id,
            topic_id=request.chapter_id,
            difficulty=request.difficulty,
            duration=request.duration,
            total_marks=0,  # Will be calculated based on questions
            created_by=current_user.id
        )
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        
        # Create questions in database
        total_marks = 0
        for i, question_data in enumerate(questions):
            print(f"Processing question {i+1}: {question_data}")
            if not isinstance(question_data, dict):
                print(f"Question {i+1} is not a dictionary: {type(question_data)}")
                continue
                
            # Validate required fields
            required_fields = ["question", "type", "options", "correctAnswer", "explanation"]
            missing_fields = [field for field in required_fields if field not in question_data]
            if missing_fields:
                print(f"Question {i+1} is missing fields: {missing_fields}")
                continue
            
            # Map question type
            question_type_map = {
                "multiple-choice": QuestionType.MULTIPLE_CHOICE,
                "short-answer": QuestionType.SHORT_ANSWER,
                "essay": QuestionType.ESSAY,
                "true-false": QuestionType.TRUE_FALSE
            }
            
            question_type = question_type_map.get(question_data["type"], QuestionType.MULTIPLE_CHOICE)
            marks = 1  # Default marks
            
            question = Question(
                assessment_id=assessment.id,
                type=question_type,
                question=question_data["question"],
                options=question_data["options"],
                correct_answer=question_data["correctAnswer"],
                explanation=question_data["explanation"],
                marks=marks,
                order=i + 1
            )
            db.add(question)
            total_marks += marks
        
        # Update assessment total marks
        assessment.total_marks = total_marks
        db.commit()
        db.refresh(assessment)
        
        return {
            "message": "Quiz generated and saved successfully",
            "assessment_id": str(assessment.id),
            "class": class_obj.name,
            "subject": subject.name,
            "chapter": chapter.name,
            "difficulty": request.difficulty,
            "num_questions": len(questions),
            "duration": request.duration,
            "total_marks": total_marks,
            "questions": questions
        }
    except (KeyError, json.JSONDecodeError, IndexError) as e:
        # If parsing fails, return the original response with an error message
        print(f"Error parsing quiz response: {str(e)}")
        return {
            "message": "Quiz generated but there was an error parsing the questions",
            "error": str(e),
            "class": class_obj.name,
            "subject": subject.name,
            "chapter": chapter.name,
            "difficulty": request.difficulty,
            "num_questions": request.num_questions,
            "duration": request.duration,
            "raw_response": quiz_result
        }


@router.post("/exam")
async def generate_exam(
    request: ExamGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    AI generates a full formal exam paper.
    """
    # Verify class exists
    class_obj = db.query(Class).filter(Class.id == request.class_id).first()
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    # Verify subject exists
    subject = db.query(Subject).filter(Subject.id == request.subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Generate exam using AI service
    exam_result = await ai_service.generate_exam(
        class_name=class_obj.name,
        subject=subject.name,
        duration=request.duration,
        total_marks=request.total_marks,
        sections=request.sections
    )
    
    # Check for errors
    if "error" in exam_result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate exam: {exam_result['error']}"
        )
    
    # Return the generated exam
    return {
        "message": "Exam generated successfully",
        "class": class_obj.name,
        "subject": subject.name,
        "duration": request.duration,
        "total_marks": request.total_marks,
        "exam_data": exam_result
    }


@router.post("/revision")
async def generate_revision(
    request: RevisionGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    AI generates revision notes/plans.
    """
    # Verify subject exists
    subject = db.query(Subject).filter(Subject.id == request.subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Get topic names
    topics = db.query(Topic).filter(Topic.id.in_(request.topic_ids)).all()
    topic_names = [topic.name for topic in topics]
    
    # Generate revision materials using AI service
    revision_result = await ai_service.generate_revision_notes(
        subject=subject.name,
        topics=topic_names,
        revision_type=request.revision_type
    )
    
    # Check for errors
    if "error" in revision_result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate revision materials: {revision_result['error']}"
        )
    
    # Return the generated revision materials
    return {
        "message": "Revision materials generated successfully",
        "subject": subject.name,
        "topic_ids": request.topic_ids,
        "revision_type": request.revision_type,
        "revision_data": revision_result
    }


@router.post("/homework")
async def generate_homework(
    request: HomeworkGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    AI generates homework assignments and stores them in the database.
    """
    # Verify class exists
    class_obj = db.query(Class).filter(Class.id == request.class_id).first()
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    # Verify subject exists
    subject = db.query(Subject).filter(Subject.id == request.subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Verify topic exists
    topic = db.query(Topic).filter(Topic.id == request.topic_id).first()
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found"
        )
    
    # Generate homework using AI service
    homework_result = await ai_service.generate_homework(
        class_name=class_obj.name,
        subject=subject.name,
        topic=topic.name,
        difficulty=request.difficulty,
        num_questions=request.num_questions
    )
    
    # Check for errors
    if "error" in homework_result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate homework: {homework_result['error']}"
        )
    
    # Extract the questions from the AI response
    try:
        # Get the content from the first choice
        content = homework_result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Log the raw content for debugging
        print(f"Raw AI response content: {content}")
        
        # Extract JSON from the content (it might be wrapped in ```json\n```)
        import re
        json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
        if json_match:
            json_content = json_match.group(1)
            print(f"Extracted JSON content: {json_content}")
        else:
            # If no markdown formatting, try to parse the entire content as JSON
            json_content = content
            print(f"No JSON markdown found, using entire content: {json_content}")
        
        # Parse the JSON to get the questions
        import json
        questions_data = json.loads(json_content)
        questions = questions_data.get("questions", [])
        
        # Log the parsed questions for debugging
        print(f"Parsed questions: {questions}")
        
        # Create assessment in database
        from ...models.assessments import Assessment, Question, AssessmentType, QuestionType
        
        assessment = Assessment(
            title=f"{subject.name} - {topic.name} Homework",
            type=AssessmentType.WORKSHEET,  # Using worksheet type for homework
            class_id=request.class_id,
            subject_id=request.subject_id,
            topic_id=request.topic_id,
            difficulty=request.difficulty,
            duration=0,  # Homework doesn't have a time limit
            total_marks=0,  # Will be calculated based on questions
            created_by=current_user.id
        )
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        
        # Create questions in database
        total_marks = 0
        for i, question_data in enumerate(questions):
            print(f"Processing question {i+1}: {question_data}")
            if not isinstance(question_data, dict):
                print(f"Question {i+1} is not a dictionary: {type(question_data)}")
                continue
                
            # Validate required fields
            required_fields = ["question", "type", "options", "correctAnswer", "explanation"]
            missing_fields = [field for field in required_fields if field not in question_data]
            if missing_fields:
                print(f"Question {i+1} is missing fields: {missing_fields}")
                continue
            
            # Map question type
            question_type_map = {
                "multiple-choice": QuestionType.MULTIPLE_CHOICE,
                "short-answer": QuestionType.SHORT_ANSWER,
                "essay": QuestionType.ESSAY,
                "true-false": QuestionType.TRUE_FALSE
            }
            
            question_type = question_type_map.get(question_data["type"], QuestionType.MULTIPLE_CHOICE)
            marks = 1  # Default marks
            
            question = Question(
                assessment_id=assessment.id,
                type=question_type,
                question=question_data["question"],
                options=question_data["options"],
                correct_answer=question_data["correctAnswer"],
                explanation=question_data["explanation"],
                marks=marks,
                order=i + 1
            )
            db.add(question)
            total_marks += marks
        
        # Update assessment total marks
        assessment.total_marks = total_marks
        db.commit()
        db.refresh(assessment)
        
        return {
            "message": "Homework generated and saved successfully",
            "assessment_id": str(assessment.id),
            "class": class_obj.name,
            "subject": subject.name,
            "topic": topic.name,
            "difficulty": request.difficulty,
            "num_questions": len(questions),
            "total_marks": total_marks,
            "homework_data": homework_result
        }
    except (KeyError, json.JSONDecodeError, IndexError) as e:
        # If parsing fails, return the original response with an error message
        print(f"Error parsing homework response: {str(e)}")
        return {
            "message": "Homework generated but there was an error parsing the questions",
            "error": str(e),
            "class": class_obj.name,
            "subject": subject.name,
            "topic": topic.name,
            "difficulty": request.difficulty,
            "num_questions": request.num_questions,
            "raw_response": homework_result
        }


@router.post("/content/generate-notes")
async def generate_notes(
    request: ContentGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    AI generates teacher lecture notes.
    """
    # Verify class exists
    class_obj = db.query(Class).filter(Class.id == request.class_id).first()
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    # Verify subject exists
    subject = db.query(Subject).filter(Subject.id == request.subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Get topic name if provided
    topic_name = ""
    if "topic_id" in request.additional_info and request.additional_info["topic_id"]:
        topic = db.query(Topic).filter(Topic.id == request.additional_info["topic_id"]).first()
        if topic:
            topic_name = topic.name
    
    # Generate teacher notes using AI service
    notes_result = await ai_service.generate_teacher_notes(
        class_name=class_obj.name,
        subject=subject.name,
        topic=topic_name,
        additional_info=request.additional_info
    )
    
    # Check for errors
    if "error" in notes_result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate teacher notes: {notes_result['error']}"
        )
    
    # Return the generated notes
    return {
        "message": "Teacher notes generated successfully",
        "class": class_obj.name,
        "subject": subject.name,
        "content_type": request.content_type,
        "additional_info": request.additional_info,
        "notes_data": notes_result
    }