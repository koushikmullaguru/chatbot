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
    sections = db.query(Section).filter(Section.class_id == class_id).all()
    return sections


@router.get("/subjects", response_model=List[SubjectResponse])
def get_subjects(
    class_id: str = Query(..., description="Class ID to get subjects for"),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get subjects for a class (query: class_id).
    """
    subjects = db.query(Subject).filter(Subject.class_id == class_id).all()
    return subjects


@router.get("/chapters", response_model=List[ChapterResponse])
def get_chapters(
    subject_id: str = Query(..., description="Subject ID to get chapters for"),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get chapters for a subject (query: subject_id).
    """
    chapters = db.query(Chapter).filter(Chapter.subject_id == subject_id).all()
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
    if chapter_id:
        topics = db.query(Topic).filter(Topic.chapter_id == chapter_id).all()
    elif subject_id:
        # Get all topics for a subject (through chapters)
        topics = (
            db.query(Topic)
            .join(Chapter)
            .filter(Chapter.subject_id == subject_id)
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
    sub_topics = db.query(SubTopic).filter(SubTopic.topic_id == topic_id).all()
    return sub_topics