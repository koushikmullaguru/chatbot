from typing import List, Optional, Any
from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, field_validator


# Task schemas
class TaskBase(BaseModel):
    student_profile_id: str
    subject_id: str
    title: str
    due_date: Optional[date] = None
    priority: str = "medium"
    status: str = "pending"


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    due_date: Optional[date] = None
    priority: Optional[str] = None
    status: Optional[str] = None


class TaskResponse(TaskBase):
    id: str

    @field_validator('id', 'student_profile_id', 'subject_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v: Any) -> Any:
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


# Report Card schemas
class ReportCardBase(BaseModel):
    student_profile_id: str
    term: str
    year: str
    percentage: Optional[float] = None
    rank: Optional[int] = None


class ReportCardCreate(ReportCardBase):
    pass


class ReportCardUpdate(BaseModel):
    percentage: Optional[float] = None
    rank: Optional[int] = None


class ReportCardResponse(ReportCardBase):
    id: str

    @field_validator('id', 'student_profile_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v: Any) -> Any:
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


# Subject Grade schemas
class SubjectGradeBase(BaseModel):
    report_card_id: str
    subject_id: str
    grade: Optional[str] = None
    marks: Optional[int] = None


class SubjectGradeCreate(SubjectGradeBase):
    pass


class SubjectGradeUpdate(BaseModel):
    grade: Optional[str] = None
    marks: Optional[int] = None


class SubjectGradeResponse(SubjectGradeBase):
    id: str

    @field_validator('id', 'report_card_id', 'subject_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v: Any) -> Any:
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


# Study Session schemas
class StudySessionBase(BaseModel):
    student_profile_id: str
    subject_id: str
    mode: str
    duration: int
    performance_score: Optional[float] = None


class StudySessionCreate(StudySessionBase):
    pass


class StudySessionUpdate(BaseModel):
    duration: Optional[int] = None
    performance_score: Optional[float] = None


class StudySessionResponse(StudySessionBase):
    id: str

    @field_validator('id', 'student_profile_id', 'subject_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v: Any) -> Any:
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


# Response with nested data
class ReportCardWithSubjectGrades(ReportCardResponse):
    subject_grades: List[SubjectGradeResponse] = []

    class Config:
        from_attributes = True


# Performance metrics
class WeeklyPerformanceMetrics(BaseModel):
    total_study_time: int
    average_performance_score: float
    completed_tasks: int
    pending_tasks: int


class StudentPerformanceReport(BaseModel):
    student_profile_id: str
    report_cards: List[ReportCardWithSubjectGrades] = []
    study_sessions: List[StudySessionResponse] = []
    tasks: List[TaskResponse] = []
    weekly_metrics: WeeklyPerformanceMetrics


class TeacherInsights(BaseModel):
    class_id: str
    subject_id: Optional[str] = None
    student_count: int
    average_performance: float
    top_performers: List[dict] = []
    struggling_students: List[dict] = []


class ParentDashboard(BaseModel):
    parent_id: str
    students: List[dict] = []
    weekly_metrics: List[dict] = []