from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
import json
import re

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
    question_types: List[str] = ["multiple-choice", "short-answer", "long-answer"]
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
    question_types: List[str] = ["multiple-choice", "short-answer", "long-answer"]


class ContentGenerateRequest(BaseModel):
    class_id: str
    subject_id: str
    topic_id: str
    content_type: str = "notes"
    additional_info: Dict[str, Any] = {}


class WorksheetGenerateRequest(BaseModel):
    class_id: str
    subject_id: str
    chapter_id: str
    difficulty: str = "medium"
    num_questions: int = 10
    question_types: List[str] = ["multiple-choice", "short-answer", "long-answer"]
    duration: int = 30  # Default duration of 30 minutes


def fix_json_content(json_content: str) -> str:
    """
    Fix common JSON issues in the AI response.
    """
    # Fix LaTeX inline math: \( ... \) -> $$ ... $$
    fixed_json_content = re.sub(r'\\\\\((.*?)\\\\\)', r'$$\1$$', json_content)
    
    # Fix LaTeX display math: \[ ... \] -> $ ... $
    fixed_json_content = re.sub(r'\\\\\[(.*?)\\\\\]', r'$\1$', fixed_json_content)
    
    # Fix single backslash escapes that are causing issues
    fixed_json_content = re.sub(r'\\\\([(){}\[\]])', r'\1', fixed_json_content)
    
    # Fix escaped quotes within the JSON
    fixed_json_content = re.sub(r'\\\\\"', r'\\"', fixed_json_content)
    
    # Fix any remaining double backslashes that aren't part of valid JSON escapes
    fixed_json_content = re.sub(r'\\\\(?!["\\/bfnrt])', r'\\\\', fixed_json_content)
    
    # Fix trailing commas in objects and arrays
    fixed_json_content = re.sub(r',(\s*[}\]])', r'\1', fixed_json_content)
    
    # Try to fix missing quotes around property names
    fixed_json_content = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', fixed_json_content)
    
    return fixed_json_content


def extract_json_from_content(content: str) -> Dict[str, Any]:
    """
    Extract and parse JSON from AI response content.
    """
    # Log the raw content for debugging
    print(f"Raw AI response content: {content}")
    
    # Check if content is empty
    if not content or content.strip() == "":
        raise ValueError("Empty response from AI service")
    
    # Extract JSON from the content (it might be wrapped in ```json\n```)
    json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
    if json_match:
        json_content = json_match.group(1)
        print(f"Extracted JSON content: {json_content}")
    else:
        # If no markdown formatting, try to parse the entire content as JSON
        json_content = content
        print(f"No JSON markdown found, using entire content: {json_content}")
    
    # Check if json_content is empty
    if not json_content or json_content.strip() == "":
        raise ValueError("Empty JSON content in AI response")
    
    # Try to parse the JSON
    try:
        questions_data = json.loads(json_content)
        print("Successfully parsed JSON")
        return questions_data
    except json.JSONDecodeError as e:
        print(f"Initial JSON parsing failed: {str(e)}")
        
        # Try to fix common JSON issues
        fixed_json_content = fix_json_content(json_content)
        
        try:
            questions_data = json.loads(fixed_json_content)
            print("Successfully parsed JSON after fixing common issues")
            return questions_data
        except json.JSONDecodeError as second_error:
            print(f"Second JSON parsing attempt failed: {str(second_error)}")
            
            # If still failing, try a more aggressive approach
            try:
                # Replace all LaTeX-style escapes with plain text
                fixed_json_content = re.sub(r'\\\\[a-zA-Z]', '', fixed_json_content)
                fixed_json_content = re.sub(r'\\\\[^"\\/bfnrt]', '', fixed_json_content)
                questions_data = json.loads(fixed_json_content)
                print("Successfully parsed JSON after aggressive escape fixing")
                return questions_data
            except json.JSONDecodeError as third_error:
                # If all attempts fail, return the error
                raise ValueError(f"Failed to parse JSON even after fixing escapes: {str(e)}. Second error: {str(second_error)}. Third error: {str(third_error)}")


def get_question_type_enum_values(db: Session) -> List[str]:
    """
    Get the actual enum values from the database.
    """
    try:
        # Query the database to get the enum values
        result = db.execute(text("""
            SELECT e.enumlabel 
            FROM pg_enum e 
            JOIN pg_type t ON e.enumtypid = t.oid 
            WHERE t.typname = 'questiontype'
        """))
        
        enum_values = [row[0] for row in result]
        print(f"Database enum values: {enum_values}")
        return enum_values
    except Exception as e:
        print(f"Error getting enum values: {str(e)}")
        # Return default values if query fails
        return [
            "MULTIPLE_CHOICE",
            "SHORT_ANSWER",
            "LONG_ANSWER",
            "ESSAY",
            "TRUE_FALSE",
            "FILL_BLANK",
            "MATCHING"
        ]


def map_question_type_to_db_enum(question_type: str, enum_values: List[str]) -> str:
    """
    Map the question type from the AI response to the database enum value.
    """
    # Create a mapping from lowercase to uppercase
    type_mapping = {
        "multiple-choice": "MULTIPLE_CHOICE",
        "short-answer": "SHORT_ANSWER",
        "long-answer": "LONG_ANSWER",
        "essay": "ESSAY",
        "true-false": "TRUE_FALSE",
        "fill-blank": "FILL_BLANK",
        "matching": "MATCHING"
    }
    
    # Get the mapped value
    mapped_type = type_mapping.get(question_type)
    
    # Check if the mapped type is in the database enum
    if mapped_type and mapped_type in enum_values:
        return mapped_type
    
    # If not found, use the first enum value as default
    if enum_values:
        print(f"Question type '{question_type}' mapped to '{mapped_type}' not in database enum values: {enum_values}")
        print(f"Using default enum value: {enum_values[0]}")
        return enum_values[0]
    
    # If no enum values, return the original mapped type
    return mapped_type or question_type


@router.post("/worksheet")
async def generate_worksheet(
    request: WorksheetGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    AI generates a worksheet with multiple question types and stores it in the database.
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
    
    # Get the actual enum values from the database
    enum_values = get_question_type_enum_values(db)
    
    # Generate worksheet using AI service
    worksheet_result = await ai_service.generate_quiz(
        subject=subject.name,
        topic=chapter.name,
        difficulty=request.difficulty,
        num_questions=request.num_questions,
        question_types=request.question_types,
        duration=request.duration
    )
    
    # Check for errors
    if "error" in worksheet_result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate worksheet: {worksheet_result['error']}"
        )
    
    # Extract the questions from the AI response
    try:
        # Get the content from the first choice
        content = worksheet_result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Extract and parse JSON from content
        questions_data = extract_json_from_content(content)
        
        questions = questions_data.get("questions", [])
        
        # Log the parsed questions for debugging
        print(f"Parsed questions: {questions}")
        
        # Check if questions array is empty
        if not questions:
            raise ValueError("No questions found in AI response")
        
        # Create assessment in database
        from ...models.assessments import Assessment, Question, AssessmentType
        
        # First, check if there's a topic for this chapter
        from ...models.academic_hierarchy import Topic
        topic = db.query(Topic).filter(Topic.chapter_id == request.chapter_id).first()
        
        assessment = Assessment(
            title=f"{subject.name} - {chapter.name} Worksheet",
            type=AssessmentType.WORKSHEET,
            class_id=request.class_id,
            subject_id=request.subject_id,
            topic_id=topic.id if topic else None,  # Use topic_id if exists, otherwise None
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
        db_questions = []
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
            
            # Map question type to database enum value
            question_type_str = map_question_type_to_db_enum(question_data["type"], enum_values)
            
            # Assign marks based on question type
            if question_type_str in ["LONG_ANSWER", "ESSAY"]:
                marks = 3
            elif question_type_str in ["SHORT_ANSWER", "MATCHING"]:
                marks = 2
            else:  # MCQ, True/False, Fill in the blanks
                marks = 1
            
            question = Question(
                assessment_id=assessment.id,
                type=question_type_str,
                question=question_data["question"],
                options=question_data["options"],
                correct_answer=question_data["correctAnswer"],
                explanation=question_data["explanation"],
                marks=marks,
                order=i + 1
            )
            db.add(question)
            db.flush()  # Flush to get the ID without committing
            total_marks += marks
            
            # Add the database question ID to the question data
            question_data_with_id = {
                **question_data,
                "id": str(question.id)  # Add the database question ID
            }
            db_questions.append(question_data_with_id)
        
        # Update assessment total marks
        assessment.total_marks = total_marks
        db.commit()
        db.refresh(assessment)
        
        return {
            "message": "Worksheet generated and saved successfully",
            "assessment_id": str(assessment.id),
            "class": class_obj.name,
            "subject": subject.name,
            "chapter": chapter.name,
            "difficulty": request.difficulty,
            "num_questions": len(db_questions),
            "duration": request.duration,
            "total_marks": total_marks,
            "questions": db_questions
        }
    except (KeyError, json.JSONDecodeError, IndexError, ValueError) as e:
        # If parsing fails, return the original response with an error message
        import traceback
        print(f"Error parsing worksheet response: {str(e)}")
        print(f"Full traceback: {traceback.format_exc()}")
        return {
            "message": "Worksheet generated but there was an error parsing the questions",
            "error": str(e),
            "class": class_obj.name,
            "subject": subject.name,
            "chapter": chapter.name,
            "difficulty": request.difficulty,
            "num_questions": request.num_questions,
            "duration": request.duration,
            "raw_response": worksheet_result
        }


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
    
    # Get the actual enum values from the database
    enum_values = get_question_type_enum_values(db)
    
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
        
        # Extract and parse JSON from content
        questions_data = extract_json_from_content(content)
        
        questions = questions_data.get("questions", [])
        
        # Log the parsed questions for debugging
        print(f"Parsed questions: {questions}")
        
        # Check if questions array is empty
        if not questions:
            raise ValueError("No questions found in AI response")
        
        # Create assessment in database
        from ...models.assessments import Assessment, Question, AssessmentType
        
        # First, check if there's a topic for this chapter
        from ...models.academic_hierarchy import Topic
        topic = db.query(Topic).filter(Topic.chapter_id == request.chapter_id).first()
        
        assessment = Assessment(
            title=f"{subject.name} - {chapter.name} Quiz",
            type=AssessmentType.QUIZ,
            class_id=request.class_id,
            subject_id=request.subject_id,
            topic_id=topic.id if topic else None,  # Use topic_id if exists, otherwise None
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
        db_questions = []
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
            
            # Map question type to database enum value
            question_type_str = map_question_type_to_db_enum(question_data["type"], enum_values)
            
            # Assign marks based on question type
            if question_type_str in ["LONG_ANSWER", "ESSAY"]:
                marks = 3
            elif question_type_str in ["SHORT_ANSWER", "MATCHING"]:
                marks = 2
            else:  # MCQ, True/False, Fill in the blanks
                marks = 1
            
            question = Question(
                assessment_id=assessment.id,
                type=question_type_str,
                question=question_data["question"],
                options=question_data["options"],
                correct_answer=question_data["correctAnswer"],
                explanation=question_data["explanation"],
                marks=marks,
                order=i + 1
            )
            db.add(question)
            db.flush()  # Flush to get the ID without committing
            total_marks += marks
            
            # Add the database question ID to the question data
            question_data_with_id = {
                **question_data,
                "id": str(question.id)  # Add the database question ID
            }
            db_questions.append(question_data_with_id)
        
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
            "num_questions": len(db_questions),
            "duration": request.duration,
            "total_marks": total_marks,
            "questions": db_questions
        }
    except (KeyError, json.JSONDecodeError, IndexError, ValueError) as e:
        # If parsing fails, return the original response with an error message
        import traceback
        print(f"Error parsing quiz response: {str(e)}")
        print(f"Full traceback: {traceback.format_exc()}")
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
    
    # Get the actual enum values from the database
    enum_values = get_question_type_enum_values(db)
    
    # Generate homework using AI service
    homework_result = await ai_service.generate_quiz(
        subject=subject.name,
        topic=topic.name,
        difficulty=request.difficulty,
        num_questions=request.num_questions,
        question_types=request.question_types,
        duration=0  # Homework doesn't have a time limit
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
        
        # Extract and parse JSON from content
        questions_data = extract_json_from_content(content)
        
        questions = questions_data.get("questions", [])
        
        # Log the parsed questions for debugging
        print(f"Parsed questions: {questions}")
        
        # Create assessment in database
        from ...models.assessments import Assessment, Question, AssessmentType
        
        # First, check if the topic exists
        from ...models.academic_hierarchy import Topic
        topic = db.query(Topic).filter(Topic.id == request.topic_id).first()
        
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found"
            )
        
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
            
            # Map question type to database enum value
            question_type_str = map_question_type_to_db_enum(question_data["type"], enum_values)
            
            # Assign marks based on question type
            if question_type_str in ["LONG_ANSWER", "ESSAY"]:
                marks = 3
            elif question_type_str in ["SHORT_ANSWER", "MATCHING"]:
                marks = 2
            else:  # MCQ, True/False, Fill in the blanks
                marks = 1
            
            question = Question(
                assessment_id=assessment.id,
                type=question_type_str,
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