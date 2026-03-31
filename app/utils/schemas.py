from pydantic import BaseModel, Field
from typing import Optional

# --- Auth Request Schemas ---

class SendOTPRequest(BaseModel):
    phone_number: str = Field(..., description="Mobile number with country code (e.g., +919876543210)")

class VerifyOTPRequest(BaseModel):
    phone_number: str = Field(..., description="Mobile number with country code (e.g., +919876543210)")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP")

class UserRegistrationRequest(BaseModel):
    phone_number: str = Field(..., description="Mobile number with country code")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    dob: str = Field(..., description="Date of birth (YYYY-MM-DD)")
    gender: str = Field(..., description="Gender (male/female/other)")
    address: str = Field(..., description="Address")
    role: str = Field(default="user", description="User role")

# --- Auth Response Schemas ---

class OTPSentResponse(BaseModel):
    success: bool = True
    message: str
    expires_in: int
    phone_number: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    registered: bool
    requires_registration: bool = False

# --- Other Schemas (Preserved) ---

class PredictionResult(BaseModel):
    label: str
    confidence: float

class AnimalRecognitionResponse(BaseModel):
    animal: PredictionResult
    breed: PredictionResult
    disease: PredictionResult

class ErrorResponse(BaseModel):
    detail: str
    status_code: int
