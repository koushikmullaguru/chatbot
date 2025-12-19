from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, field_validator


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

    @field_validator('id', 'created_by_id', 'class_id', 'subject_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v: Any) -> Any:
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True