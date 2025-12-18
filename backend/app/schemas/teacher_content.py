from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel


# Teacher Content Unit schemas
class TeacherContentUnitBase(BaseModel):
    created_by_id: str
    class_id: str
    subject_id: str
    type: str
    title: str
    content_data: Optional[Dict[str, Any]] = None


class TeacherContentUnitCreate(TeacherContentUnitBase):
    pass


class TeacherContentUnitUpdate(BaseModel):
    title: Optional[str] = None
    content_data: Optional[Dict[str, Any]] = None


class TeacherContentUnitResponse(TeacherContentUnitBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True