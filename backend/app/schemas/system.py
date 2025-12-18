from typing import Optional
from datetime import datetime
from pydantic import BaseModel


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

    class Config:
        from_attributes = True