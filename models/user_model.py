from pydantic import BaseModel, Field
from typing import Optional

class User(BaseModel):
    """
    Base model for the User model.
    This model is used to define the attributes of a user.
    """
    user_name: str = Field(..., min_length=3, max_length=50)
    user_dob: str = Field(...)
    user_gender: str = Field(...)
    user_address: str = Field(..., min_length=5, max_length=100)
    user_phone_number: str = Field(...)
    role: str = Field(default="user", description="Role of the user (user/admin)")

class UserPublic(BaseModel):
    """
    Public user model for list endpoints where some fields may be missing.
    """
    user_name: Optional[str] = None
    user_dob: Optional[str] = None
    user_gender: Optional[str] = None
    user_address: Optional[str] = None
    user_phone_number: Optional[str] = None
    role: Optional[str] = Field(default="user", description="Role of the user (user/admin)")
