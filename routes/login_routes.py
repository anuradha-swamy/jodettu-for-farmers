from fastapi import APIRouter, Depends, Body
from services.login_services import LoginServices
from general.security import Security
from models.user_model import User, UserPublic
from app.utils.schemas import SendOTPRequest, VerifyOTPRequest, OTPSentResponse, TokenResponse, UserRegistrationRequest
from typing import List

router = APIRouter(tags=["Authentication"]) # Ensure all routes are under Authentication tag
services = LoginServices()

@router.post("/send-otp", response_model=OTPSentResponse)
async def send_otp(request: SendOTPRequest):
    """
    Step 1: Send OTP
    - Sends OTP via Twilio.
    - Returns success message and a temporary session token.
    """
    return await services.send_otp(request.phone_number)

@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(request: VerifyOTPRequest):
    """
    Step 2: Verify OTP
    - Verifies the OTP using the session token from send-otp step.
    - If valid, generates and returns the JWT access token.
    """
    return await services.verify_otp(request.phone_number, request.otp)

@router.post("/logout")
async def logout(current_user: dict = Depends(Security.get_current_user)):
    """
    Logs out the user.
    Since JWTs are stateless, this endpoint mainly serves as a confirmation
    for the client to clear the token from local storage.
    """
    return {"message": "Logout successful"}

@router.delete("/delete-user/{phone_number}")
async def delete_user(
    phone_number: str,
    current_user: dict = Depends(Security.get_current_admin_user)
):
    """
    Deletes a user and their associated data by phone number.
    Only accessible by admins.
    """
    return await services.delete_user_by_phone(phone_number)

@router.post("/register")
async def register_user(
    registration_data: UserRegistrationRequest,
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Register a new user with detailed information.
    This endpoint is called after OTP verification for new users.
    """
    phone_number = current_user["username"]
    return await services.register_user(registration_data.dict(), phone_number)

@router.get("/users", response_model=List[UserPublic])
async def get_all_users(current_user: dict = Depends(Security.get_current_user)):
    return await services.get_all_registered_users()

@router.put("/edit-profile")
async def edit_profile(
    profile_data: dict = Body(...),
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Edit user profile details.
    Allows users to update their personal information.
    """
    try:
        phone_number = current_user["username"]
        return await services.edit_user_profile(phone_number, profile_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")

@router.get("/profile")
async def get_profile(current_user: dict = Depends(Security.get_current_user)):
    """
    Get current user's profile details.
    """
    try:
        phone_number = current_user["username"]
        return await services.get_user_profile(phone_number)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")
