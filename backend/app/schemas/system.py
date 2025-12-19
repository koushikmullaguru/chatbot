from typing import Optional, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, field_validator


# OTP Verification schemas
class OtpVerificationBase(BaseModel):
    email: str
    otp: str
    expires_at: datetime
    verified: bool = False


class OtpVerificationCreate(OtpVerificationBase):
    pass


class OtpVerificationUpdate(BaseModel):
    verified: Optional[bool] = None


class OtpVerificationResponse(OtpVerificationBase):
    id: str

    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v: Any) -> Any:
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


# User Session schemas
class UserSessionBase(BaseModel):
    user_id: str
    token: str
    expires_at: datetime


class UserSessionCreate(UserSessionBase):
    pass


class UserSessionUpdate(BaseModel):
    token: Optional[str] = None
    expires_at: Optional[datetime] = None


class UserSessionResponse(UserSessionBase):
    id: str

    @field_validator('id', 'user_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v: Any) -> Any:
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True