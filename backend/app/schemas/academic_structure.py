from typing import Optional, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, field_validator


# Syllabus Document schemas
class SyllabusDocumentBase(BaseModel):
    class_id: str
    subject_id: str
    file_url: str
    ingestion_status: str = "Pending"


class SyllabusDocumentCreate(SyllabusDocumentBase):
    pass


class SyllabusDocumentUpdate(BaseModel):
    file_url: Optional[str] = None
    ingestion_status: Optional[str] = None


class SyllabusDocumentResponse(SyllabusDocumentBase):
    id: str

    @field_validator('id', 'class_id', 'subject_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v: Any) -> Any:
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True