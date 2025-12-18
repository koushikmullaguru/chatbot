from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel


# Assessment schemas
class AssessmentBase(BaseModel):
    title: str
    type: str
    class_id: str
    subject_id: str
    topic_id: Optional[str] = None
    difficulty: str = "medium"
    duration: Optional[int] = None
    total_marks: Optional[int] = None


class AssessmentCreate(AssessmentBase):
    created_by: str


class AssessmentUpdate(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = None
    difficulty: Optional[str] = None
    duration: Optional[int] = None
    total_marks: Optional[int] = None


class AssessmentResponse(AssessmentBase):
    id: str
    created_by: str

    class Config:
        from_attributes = True


# Question schemas
class QuestionBase(BaseModel):
    assessment_id: str
    type: str
    question: str
    options: Optional[List[str]] = None
    correct_answer: str
    explanation: Optional[str] = None
    marks: int = 1
    order: int


class QuestionCreate(QuestionBase):
    pass


class QuestionUpdate(BaseModel):
    question: Optional[str] = None
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    marks: Optional[int] = None
    order: Optional[int] = None


class QuestionResponse(QuestionBase):
    id: str

    class Config:
        from_attributes = True


# Assessment Result schemas
class AssessmentResultBase(BaseModel):
    assessment_id: str
    student_profile_id: str
    total_score: float
    percentage: float
    completed_at: Optional[datetime] = None


class AssessmentResultCreate(AssessmentResultBase):
    pass


class AssessmentResultUpdate(BaseModel):
    total_score: Optional[float] = None
    percentage: Optional[float] = None
    completed_at: Optional[datetime] = None


class AssessmentResultResponse(AssessmentResultBase):
    id: str

    class Config:
        from_attributes = True


# Student Answer schemas
class StudentAnswerBase(BaseModel):
    assessment_result_id: str
    question_id: str
    answer: str
    score: float


class StudentAnswerCreate(StudentAnswerBase):
    pass


class StudentAnswerUpdate(BaseModel):
    answer: Optional[str] = None
    score: Optional[float] = None


class StudentAnswerResponse(StudentAnswerBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


# Response with nested data
class AssessmentWithQuestions(AssessmentResponse):
    questions: List[QuestionResponse] = []

    class Config:
        from_attributes = True


class AssessmentResultWithStudentAnswers(AssessmentResultResponse):
    student_answers: List[StudentAnswerResponse] = []

    class Config:
        from_attributes = True