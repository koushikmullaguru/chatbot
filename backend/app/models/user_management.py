from sqlalchemy import Column, String, Boolean, DateTime, Enum, ForeignKey, Text, Integer, Date, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from datetime import datetime

from ..core.database import Base
from ..utils.grade_utils import normalize_grade


class UserType(str, enum.Enum):
    TEACHER = "teacher"
    PARENT = "parent"
    STUDENT = "student"


class TeacherRole(str, enum.Enum):
    SUBJECT_TEACHER = "subject-teacher"
    CLASS_HEAD = "class-head"
    PRINCIPAL = "principal"


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    password = Column(String(255))
    user_type = Column(Enum(UserType), nullable=False)
    grade = Column(String(20))
    subject = Column(String(100))
    teacher_role = Column(Enum(TeacherRole))
    teacher_subject = Column(String(100))
    teacher_class = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student_profiles = relationship("StudentProfile", back_populates="user")
    parent_student_relations = relationship("ParentStudentRelation", foreign_keys="ParentStudentRelation.parent_id", back_populates="parent")
    chat_sessions = relationship("ChatSession", back_populates="user")
    teacher_content_units = relationship("TeacherContentUnit", back_populates="created_by")
    assessments = relationship("Assessment", back_populates="created_by_user")
    user_sessions = relationship("UserSession", back_populates="user")
    
    @property
    def normalized_grade(self):
        """Return the grade in normalized format (Grade X)"""
        if self.grade:
            return normalize_grade(self.grade)
        return None


class StudentProfile(Base):
    __tablename__ = "student_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    name = Column(String(100))
    grade = Column(String(20))
    avatar = Column(String(255))
    pin = Column(String(10))
    roll_number = Column(String(50))
    date_of_birth = Column(Date)
    blood_group = Column(String(5))
    admission_date = Column(Date)
    email = Column(String(255))
    phone = Column(String(20))
    address = Column(Text)
    parent_name = Column(String(100))
    parent_email = Column(String(255))
    parent_phone = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="student_profiles")
    parent_student_relations = relationship("ParentStudentRelation", back_populates="student_profile")
    student_interests = relationship("StudentInterest", back_populates="student_profile")
    student_achievements = relationship("StudentAchievement", back_populates="student_profile")
    chat_sessions = relationship("ChatSession", back_populates="student_profile")
    tasks = relationship("Task", back_populates="student_profile")
    report_cards = relationship("ReportCard", back_populates="student_profile")
    assessment_results = relationship("AssessmentResult", back_populates="student_profile")
    study_sessions = relationship("StudySession", back_populates="student_profile")
    
    @property
    def normalized_grade(self):
        """Return the grade in normalized format (Grade X)"""
        if self.grade:
            return normalize_grade(self.grade)
        return None


class ParentStudentRelation(Base):
    __tablename__ = "parent_student_relations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    student_profile_id = Column(UUID(as_uuid=True), ForeignKey("student_profiles.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    parent = relationship("User", back_populates="parent_student_relations")
    student_profile = relationship("StudentProfile", back_populates="parent_student_relations")


class StudentInterest(Base):
    __tablename__ = "student_interests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_profile_id = Column(UUID(as_uuid=True), ForeignKey("student_profiles.id"))
    interest_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    student_profile = relationship("StudentProfile", back_populates="student_interests")


class StudentAchievement(Base):
    __tablename__ = "student_achievements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_profile_id = Column(UUID(as_uuid=True), ForeignKey("student_profiles.id"))
    title = Column(String(100))
    date = Column(Date)
    icon = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    student_profile = relationship("StudentProfile", back_populates="student_achievements")