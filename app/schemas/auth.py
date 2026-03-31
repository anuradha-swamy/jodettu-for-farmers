from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SendOTPRequest(BaseModel):
    phone_number: str = Field(..., min_length=10, max_length=15, description="Mobile number with country code")


class SendOTPResponse(BaseModel):
    success: bool = True
    message: str
    masked_phone: str
    otp_expiry_minutes: int
    registered: bool = False


class VerifyOTPRequest(BaseModel):
    phone_number: str = Field(..., min_length=10, max_length=15)
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP")


class VerifyOTPResponse(BaseModel):
    success: bool = True
    message: str
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    registered: bool = False


class TokenData(BaseModel):
    phone_number: Optional[str] = None


class UserProfile(BaseModel):
    user_id: str
    user_name: str
    user_phone_number: str
    user_dob: str
    user_gender: str
    user_address: str
    registered: bool = True
