from typing import Optional
from datetime import datetime
from pydantic import BaseModel


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

    class Config:
        from_attributes = True