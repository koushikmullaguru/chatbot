from sqlalchemy import Column, String, ForeignKey, Enum, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum
from datetime import datetime

from ..core.database import Base


class ContentType(str, enum.Enum):
    NOTES = "notes"
    WORKSHEET = "worksheet"
    EXAM_TEMPLATE = "exam-template"


class TeacherContentUnit(Base):
    __tablename__ = "teacher_content_units"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"))
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"))
    type = Column(Enum(ContentType), nullable=False)
    title = Column(String(200), nullable=False)
    content_data = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    created_by = relationship("User", back_populates="teacher_content_units")
    class_ = relationship("Class", back_populates="teacher_content_units")
    subject = relationship("Subject", back_populates="teacher_content_units")