from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel


# Chat Session schemas
class ChatSessionBase(BaseModel):
    user_id: str
    student_profile_id: str
    mode: str
    title: Optional[str] = None


class ChatSessionCreate(ChatSessionBase):
    pass


class ChatSessionUpdate(BaseModel):
    title: Optional[str] = None
    mode: Optional[str] = None


class ChatSessionResponse(ChatSessionBase):
    id: str
    created_at: datetime
    updated_at: datetime

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

    class Config:
        from_attributes = True


# Response with nested data
class ChatSessionWithMessages(ChatSessionResponse):
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True