from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...api.deps import get_current_user
from ...models.user_management import User
from ...models.academic_hierarchy import Class, Section, Subject, Chapter, Topic, SubTopic
from ...schemas.academic_hierarchy import (
    ClassResponse, SectionResponse, SubjectResponse, 
    ChapterResponse, TopicResponse, SubTopicResponse,
    ClassWithSubjects, SubjectWithChapters, ChapterWithTopics, TopicWithSubTopics
)

router = APIRouter()


@router.get("/classes", response_model=List[ClassResponse])
def get_all_classes(
    db: Session = Depends(get_db)
) -> Any:
    """
    Get all available classes/grades.
    """
    classes = db.query(Class).all()
    return classes


@router.get("/sections", response_model=List[SectionResponse])
def get_sections(
    class_id: str = Query(..., description="Class ID to get sections for"),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get sections for a class (query: class_id).
    """
    # Check if class_id is a UUID or a class name
    import uuid
    try:
        # Try to parse as UUID
        uuid.UUID(class_id)
        # If successful, it's a UUID
        sections = db.query(Section).filter(Section.class_id == class_id).all()
    except ValueError:
        # Not a UUID, so it's a class name
        # Try to find class by name (with spaces)
        class_obj = db.query(Class).filter(Class.name == class_id).first()
        
        # If not found, try to find by name without spaces
        if not class_obj:
            # Remove spaces and try again
            class_name_no_spaces = class_id.replace(" ", "")
            class_obj = db.query(Class).filter(Class.name == class_name_no_spaces).first()
            
            # If still not found, try to find by name with spaces
            if not class_obj:
                # Add spaces between letters and numbers (e.g., "Grade10" -> "Grade 10")
                import re
                class_name_with_spaces = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', class_id)
                class_obj = db.query(Class).filter(Class.name == class_name_with_spaces).first()
        
        if not class_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Class with name '{class_id}' not found"
            )
        sections = db.query(Section).filter(Section.class_id == class_obj.id).all()
    
    return sections


@router.get("/subjects", response_model=List[SubjectResponse])
def get_subjects(
    class_id: str = Query(..., description="Class ID to get subjects for"),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get subjects for a class (query: class_id).
    """
    # Check if class_id is a UUID or a class name
    import uuid
    try:
        # Try to parse as UUID
        uuid.UUID(class_id)
        # If successful, it's a UUID
        subjects = db.query(Subject).filter(Subject.class_id == class_id).all()
    except ValueError:
        # Not a UUID, so it's a class name
        # Try to find class by name (with spaces)
        class_obj = db.query(Class).filter(Class.name == class_id).first()
        
        # If not found, try to find by name without spaces
        if not class_obj:
            # Remove spaces and try again
            class_name_no_spaces = class_id.replace(" ", "")
            class_obj = db.query(Class).filter(Class.name == class_name_no_spaces).first()
            
            # If still not found, try to find by name with spaces
            if not class_obj:
                # Add spaces between letters and numbers (e.g., "Grade10" -> "Grade 10")
                import re
                class_name_with_spaces = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', class_id)
                class_obj = db.query(Class).filter(Class.name == class_name_with_spaces).first()
        
        if not class_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Class with name '{class_id}' not found"
            )
        subjects = db.query(Subject).filter(Subject.class_id == class_obj.id).all()
    
    return subjects


@router.get("/chapters", response_model=List[ChapterResponse])
def get_chapters(
    subject_id: str = Query(..., description="Subject ID to get chapters for"),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get chapters for a subject (query: subject_id).
    """
    # Check if subject_id is a UUID or a subject name
    import uuid
    try:
        # Try to parse as UUID
        uuid.UUID(subject_id)
        # If successful, it's a UUID
        chapters = db.query(Chapter).filter(Chapter.subject_id == subject_id).all()
    except ValueError:
        # Not a UUID, so it's a subject name
        subject_obj = db.query(Subject).filter(Subject.name == subject_id).first()
        if not subject_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subject with name '{subject_id}' not found"
            )
        chapters = db.query(Chapter).filter(Chapter.subject_id == subject_obj.id).all()
    
    return chapters


@router.get("/topics", response_model=List[TopicResponse])
def get_topics(
    subject_id: Optional[str] = Query(None, description="Subject ID to get topics for"),
    chapter_id: Optional[str] = Query(None, description="Chapter ID to get topics for"),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get topics for a specific subject or chapter.
    """
    import uuid
    
    if chapter_id:
        # Check if chapter_id is a UUID or a chapter name
        try:
            uuid.UUID(chapter_id)
            # If successful, it's a UUID
            topics = db.query(Topic).filter(Topic.chapter_id == chapter_id).all()
        except ValueError:
            # Not a UUID, so it's a chapter name
            chapter_obj = db.query(Chapter).filter(Chapter.name == chapter_id).first()
            if not chapter_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Chapter with name '{chapter_id}' not found"
                )
            topics = db.query(Topic).filter(Topic.chapter_id == chapter_obj.id).all()
    elif subject_id:
        # Check if subject_id is a UUID or a subject name
        try:
            uuid.UUID(subject_id)
            # If successful, it's a UUID
            # Get all topics for a subject (through chapters)
            topics = (
                db.query(Topic)
                .join(Chapter)
                .filter(Chapter.subject_id == subject_id)
                .all()
            )
        except ValueError:
            # Not a UUID, so it's a subject name
            subject_obj = db.query(Subject).filter(Subject.name == subject_id).first()
            if not subject_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Subject with name '{subject_id}' not found"
                )
            # Get all topics for a subject (through chapters)
            topics = (
                db.query(Topic)
                .join(Chapter)
                .filter(Chapter.subject_id == subject_obj.id)
                .all()
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either subject_id or chapter_id must be provided"
        )
    
    return topics


@router.get("/sub-topics", response_model=List[SubTopicResponse])
def get_sub_topics(
    topic_id: str = Query(..., description="Topic ID to get sub-topics for"),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get granular sub-topics for a chapter.
    """
    # Check if topic_id is a UUID or a topic name
    import uuid
    try:
        # Try to parse as UUID
        uuid.UUID(topic_id)
        # If successful, it's a UUID
        sub_topics = db.query(SubTopic).filter(SubTopic.topic_id == topic_id).all()
    except ValueError:
        # Not a UUID, so it's a topic name
        topic_obj = db.query(Topic).filter(Topic.name == topic_id).first()
        if not topic_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic with name '{topic_id}' not found"
            )
        sub_topics = db.query(SubTopic).filter(SubTopic.topic_id == topic_obj.id).all()
    
    return sub_topics