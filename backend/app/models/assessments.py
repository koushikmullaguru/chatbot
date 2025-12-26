from sqlalchemy import Column, String, ForeignKey, Enum, Text, Integer, DateTime, Date, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum
from datetime import datetime

from ..core.database import Base


class AssessmentType(str, enum.Enum):
    QUIZ = "quiz"
    WORKSHEET = "worksheet"
    EXAM = "exam"


class QuestionType(str, enum.Enum):
    MULTIPLE_CHOICE = "multiple-choice"
    SHORT_ANSWER = "short-answer"
    LONG_ANSWER = "long-answer"
    ESSAY = "essay"
    TRUE_FALSE = "true-false"
    FILL_BLANK = "fill-blank"
    MATCHING = "matching"


class Difficulty(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Assessment(Base):
    __tablename__ = "assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    type = Column(Enum(AssessmentType), nullable=False)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"))
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"))
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id"))
    difficulty = Column(Enum(Difficulty), default=Difficulty.MEDIUM)
    duration = Column(Integer)  # Duration in minutes
    total_marks = Column(Integer)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    class_ = relationship("Class", back_populates="assessments")
    subject = relationship("Subject", back_populates="assessments")
    topic = relationship("Topic", back_populates="assessments")
    created_by_user = relationship("User", back_populates="assessments")
    questions = relationship("Question", back_populates="assessment")
    assessment_results = relationship("AssessmentResult", back_populates="assessment")


class Question(Base):
    __tablename__ = "questions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("assessments.id"))
    type = Column(Enum(QuestionType), nullable=False)
    question = Column(Text, nullable=False)
    options = Column(JSONB)  # For MCQ options
    correct_answer = Column(Text)  # For MCQ, it could be the option text
    explanation = Column(Text)
    marks = Column(Integer, default=1)
    order = Column(Integer)
    
    # Relationships
    assessment = relationship("Assessment", back_populates="questions")
    student_answers = relationship("StudentAnswer", back_populates="question")


class AssessmentResult(Base):
    __tablename__ = "assessment_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("assessments.id"))
    student_profile_id = Column(UUID(as_uuid=True), ForeignKey("student_profiles.id"))
    total_score = Column(Numeric(5, 2))
    percentage = Column(Numeric(5, 2))
    completed_at = Column(DateTime)
    
    # Relationships
    assessment = relationship("Assessment", back_populates="assessment_results")
    student_profile = relationship("StudentProfile", back_populates="assessment_results")
    student_answers = relationship("StudentAnswer", back_populates="assessment_result")


class StudentAnswer(Base):
    __tablename__ = "student_answers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_result_id = Column(UUID(as_uuid=True), ForeignKey("assessment_results.id"))
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"))
    answer = Column(Text)  # For MCQ, it could be the option text
    score = Column(Numeric(5, 2))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    assessment_result = relationship("AssessmentResult", back_populates="student_answers")
    question = relationship("Question", back_populates="student_answers")