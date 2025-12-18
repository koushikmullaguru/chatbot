from sqlalchemy import Column, String, ForeignKey, Enum, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum
from datetime import datetime

from ..core.database import Base


class ChatMode(str, enum.Enum):
    QA = "qa"
    QUIZ = "quiz"
    PLANNER = "planner"
    DISCUSSION = "discussion"


class SenderType(str, enum.Enum):
    USER = "user"
    AI = "ai"


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    student_profile_id = Column(UUID(as_uuid=True), ForeignKey("student_profiles.id"))
    mode = Column(Enum(ChatMode), nullable=False)
    title = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    student_profile = relationship("StudentProfile", back_populates="chat_sessions")
    messages = relationship("Message", back_populates="chat_session")


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"))
    content = Column(Text, nullable=False)
    sender_type = Column(Enum(SenderType), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    suggested_questions = Column(JSONB)
    
    # Relationships
    chat_session = relationship("ChatSession", back_populates="messages")