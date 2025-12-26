from sqlalchemy import Column, String, ForeignKey, Enum, Integer, DateTime, Date, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from datetime import datetime

from ..core.database import Base


class Priority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"


class StudyMode(str, enum.Enum):
    EXAM = "exam"
    REVISION = "revision"


class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_profile_id = Column(UUID(as_uuid=True), ForeignKey("student_profiles.id"))
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"))
    title = Column(String(200), nullable=False)
    due_date = Column(Date)
    priority = Column(Enum(Priority), default=Priority.MEDIUM)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    
    # Relationships
    student_profile = relationship("StudentProfile", back_populates="tasks")
    subject = relationship("Subject", back_populates="tasks")


class ReportCard(Base):
    __tablename__ = "report_cards"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_profile_id = Column(UUID(as_uuid=True), ForeignKey("student_profiles.id"))
    term = Column(String(50), nullable=False)
    year = Column(String(10), nullable=False)
    percentage = Column(Numeric(5, 2))
    rank = Column(Integer)
    
    # Relationships
    student_profile = relationship("StudentProfile", back_populates="report_cards")
    subject_grades = relationship("SubjectGrade", back_populates="report_card")


class SubjectGrade(Base):
    __tablename__ = "subject_grades"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_card_id = Column(UUID(as_uuid=True), ForeignKey("report_cards.id"))
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"))
    grade = Column(String(5))
    marks = Column(Integer)
    
    # Relationships
    report_card = relationship("ReportCard", back_populates="subject_grades")
    subject = relationship("Subject", back_populates="subject_grades")


class StudySession(Base):
    __tablename__ = "study_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_profile_id = Column(UUID(as_uuid=True), ForeignKey("student_profiles.id"))
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"))
    mode = Column(Enum(StudyMode), nullable=False)
    duration = Column(Integer)  # Duration in minutes
    performance_score = Column(Numeric(5, 2))  # 0-100 score
    
    # Relationships
    student_profile = relationship("StudentProfile", back_populates="study_sessions")
    subject = relationship("Subject", back_populates="study_sessions")