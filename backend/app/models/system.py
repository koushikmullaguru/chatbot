from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timedelta

from ..core.database import Base


class OtpVerification(Base):
    __tablename__ = "otp_verifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False)
    otp = Column(String(10), nullable=False)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(minutes=15))
    verified = Column(Boolean, default=False)


class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    token = Column(String(500), nullable=False)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=30))
    
    # Relationships
    user = relationship("User", back_populates="user_sessions")