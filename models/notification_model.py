from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum

class VaccinationStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"

class NotificationType(str, Enum):
    REMINDER = "reminder"
    DUE = "due"

class VaccinationRecord(BaseModel):
    """
    Model for vaccination records associated with animals.
    """
    user_id: str = Field(..., description="User ID who owns the animal")
    animal_id: str = Field(..., description="Animal ID")
    vaccine_name: str = Field(..., description="Name of the vaccine")
    next_vaccination_date: datetime = Field(..., description="Next vaccination date")
    vaccination_status: VaccinationStatus = Field(default=VaccinationStatus.PENDING, description="Vaccination status")

class Notification(BaseModel):
    """
    Model for vaccination notifications.
    """
    user_id: str = Field(..., description="User ID to receive notification")
    message: str = Field(..., description="Notification message")
    type: NotificationType = Field(..., description="Type of notification")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When notification was created")
    is_read: bool = Field(default=False, description="Whether notification has been read")
    vaccination_record_id: Optional[str] = Field(None, description="Associated vaccination record ID")

class NotificationResponse(BaseModel):
    """
    Response model for notifications with additional fields.
    """
    id: str = Field(..., description="Notification ID")
    user_id: str = Field(..., description="User ID")
    message: str = Field(..., description="Notification message")
    type: NotificationType = Field(..., description="Notification type")
    created_at: datetime = Field(..., description="Creation date")
    is_read: bool = Field(..., description="Read status")
    vaccination_record_id: Optional[str] = Field(None, description="Associated vaccination record ID")

class VaccinationSchedule(BaseModel):
    """
    Model for vaccination scheduling.
    """
    animal_id: str = Field(..., description="Animal ID")
    vaccine_name: str = Field(..., description="Vaccine name")
    scheduled_date: datetime = Field(..., description="Scheduled vaccination date")
    reminder_days: int = Field(default=10, description="Days before to send reminder")
