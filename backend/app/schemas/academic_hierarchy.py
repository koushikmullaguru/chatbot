from typing import List, Optional, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, field_validator


# Class schemas
class ClassBase(BaseModel):
    name: str


class ClassCreate(ClassBase):
    pass


class ClassResponse(ClassBase):
    id: str

    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v: Any) -> Any:
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


# Section schemas
class SectionBase(BaseModel):
    class_id: str
    name: str


class SectionCreate(SectionBase):
    pass


class SectionResponse(SectionBase):
    id: str

    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v: Any) -> Any:
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


# Subject schemas
class SubjectBase(BaseModel):
    class_id: str
    name: str


class SubjectCreate(SubjectBase):
    pass


class SubjectResponse(SubjectBase):
    id: str

    @field_validator('id', 'class_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v: Any) -> Any:
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


# Chapter schemas
class ChapterBase(BaseModel):
    subject_id: str
    name: str


class ChapterCreate(ChapterBase):
    pass


class ChapterResponse(ChapterBase):
    id: str

    @field_validator('id', 'subject_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v: Any) -> Any:
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


# Topic schemas
class TopicBase(BaseModel):
    chapter_id: str
    name: str


class TopicCreate(TopicBase):
    pass


class TopicResponse(TopicBase):
    id: str

    @field_validator('id', 'chapter_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v: Any) -> Any:
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


# SubTopic schemas
class SubTopicBase(BaseModel):
    topic_id: str
    name: str


class SubTopicCreate(SubTopicBase):
    pass


class SubTopicResponse(SubTopicBase):
    id: str

    @field_validator('id', 'topic_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v: Any) -> Any:
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


# Response with nested data
class ClassWithSubjects(ClassResponse):
    subjects: List[SubjectResponse] = []
    sections: List[SectionResponse] = []

    class Config:
        from_attributes = True


class SubjectWithChapters(SubjectResponse):
    chapters: List[ChapterResponse] = []

    class Config:
        from_attributes = True


class ChapterWithTopics(ChapterResponse):
    topics: List[TopicResponse] = []

    class Config:
        from_attributes = True


class TopicWithSubTopics(TopicResponse):
    sub_topics: List[SubTopicResponse] = []

    class Config:
        from_attributes = True