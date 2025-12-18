from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr


# User schemas
class UserBase(BaseModel):
    name: str
    email: EmailStr
    user_type: str
    grade: Optional[str] = None
    subject: Optional[str] = None
    teacher_role: Optional[str] = None
    teacher_subject: Optional[str] = None
    teacher_class: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    grade: Optional[str] = None
    subject: Optional[str] = None
    teacher_role: Optional[str] = None
    teacher_subject: Optional[str] = None
    teacher_class: Optional[str] = None


class UserResponse(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Student Profile schemas
class StudentProfileBase(BaseModel):
    name: str
    grade: str
    avatar: Optional[str] = None
    pin: str
    roll_number: str


class StudentProfileCreate(StudentProfileBase):
    user_id: str


class StudentProfileUpdate(BaseModel):
    name: Optional[str] = None
    grade: Optional[str] = None
    avatar: Optional[str] = None
    pin: Optional[str] = None
    roll_number: Optional[str] = None


class StudentProfileResponse(StudentProfileBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Parent Student Relation schemas
class ParentStudentRelationBase(BaseModel):
    parent_id: str
    student_profile_id: str


class ParentStudentRelationCreate(ParentStudentRelationBase):
    pass


class ParentStudentRelationResponse(ParentStudentRelationBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


# Student Interest schemas
class StudentInterestBase(BaseModel):
    interest_name: str


class StudentInterestCreate(StudentInterestBase):
    student_profile_id: str


class StudentInterestResponse(StudentInterestBase):
    id: str
    student_profile_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# Student Achievement schemas
class StudentAchievementBase(BaseModel):
    title: str
    date: datetime
    icon: Optional[str] = None


class StudentAchievementCreate(StudentAchievementBase):
    student_profile_id: str


class StudentAchievementResponse(StudentAchievementBase):
    id: str
    student_profile_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# Auth schemas
class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[str] = None


class OtpRequest(BaseModel):
    email: EmailStr


class OtpVerify(BaseModel):
    email: EmailStr
    otp: str


# User with related data
class UserWithStudentProfiles(UserResponse):
    student_profiles: List[StudentProfileResponse] = []

    class Config:
        from_attributes = True


class ParentWithStudentProfiles(UserResponse):
    student_profiles: List[StudentProfileResponse] = []

    class Config:
        from_attributes = True