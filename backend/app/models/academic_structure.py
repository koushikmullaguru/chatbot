from sqlalchemy import Column, String, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from datetime import datetime

from ..core.database import Base


class IngestionStatus(str, enum.Enum):
    PENDING = "Pending"
    VECTORIZED = "Vectorized"
    FAILED = "Failed"


class SyllabusDocument(Base):
    __tablename__ = "syllabus_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"))
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"))
    file_url = Column(String(500))
    ingestion_status = Column(Enum(IngestionStatus), default=IngestionStatus.PENDING)
    
    # Relationships
    class_ = relationship("Class")
    subject = relationship("Subject")