from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from ..core.database import Base


class Class(Base):
    __tablename__ = "classes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), nullable=False)
    
    # Relationships
    sections = relationship("Section", back_populates="class_")
    subjects = relationship("Subject", back_populates="class_")
    syllabus_documents = relationship("SyllabusDocument", back_populates="class_")
    teacher_content_units = relationship("TeacherContentUnit", back_populates="class_")
    assessments = relationship("Assessment", back_populates="class_")


class Section(Base):
    __tablename__ = "sections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"))
    name = Column(String(10), nullable=False)
    
    # Relationships
    class_ = relationship("Class", back_populates="sections")


class Subject(Base):
    __tablename__ = "subjects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"))
    name = Column(String(100), nullable=False)
    
    # Relationships
    class_ = relationship("Class", back_populates="subjects")
    chapters = relationship("Chapter", back_populates="subject")
    syllabus_documents = relationship("SyllabusDocument", back_populates="subject")
    teacher_content_units = relationship("TeacherContentUnit", back_populates="subject")
    assessments = relationship("Assessment", back_populates="subject")
    tasks = relationship("Task", back_populates="subject")
    subject_grades = relationship("SubjectGrade", back_populates="subject")
    study_sessions = relationship("StudySession", back_populates="subject")


class Chapter(Base):
    __tablename__ = "chapters"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"))
    name = Column(String(100), nullable=False)
    
    # Relationships
    subject = relationship("Subject", back_populates="chapters")
    topics = relationship("Topic", back_populates="chapter")


class Topic(Base):
    __tablename__ = "topics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chapter_id = Column(UUID(as_uuid=True), ForeignKey("chapters.id"))
    name = Column(String(100), nullable=False)
    
    # Relationships
    chapter = relationship("Chapter", back_populates="topics")
    sub_topics = relationship("SubTopic", back_populates="topic")
    assessments = relationship("Assessment", back_populates="topic")


class SubTopic(Base):
    __tablename__ = "sub_topics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id"))
    name = Column(String(100), nullable=False)
    
    # Relationships
    topic = relationship("Topic", back_populates="sub_topics")