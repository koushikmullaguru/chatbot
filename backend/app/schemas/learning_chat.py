from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, field_validator


# Chat Session schemas
class ChatSessionBase(BaseModel):
    student_profile_id: str
    mode: str
    title: Optional[str] = None


class ChatSessionCreate(ChatSessionBase):
    user_id: Optional[str] = None


class ChatSessionUpdate(BaseModel):
    title: Optional[str] = None
    mode: Optional[str] = None


class ChatSessionResponse(ChatSessionBase):
    id: str
    created_at: datetime
    updated_at: datetime

    @field_validator('id', 'student_profile_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v: Any) -> Any:
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


# Message schemas
class MessageBase(BaseModel):
    content: str
    sender_type: str
    suggested_questions: Optional[List[str]] = None


class MessageCreate(MessageBase):
    chat_session_id: str


class MessageResponse(MessageBase):
    id: str
    chat_session_id: str
    timestamp: datetime

    @field_validator('id', 'chat_session_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v: Any) -> Any:
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


# Response with nested data
class ChatSessionWithMessages(ChatSessionResponse):
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True