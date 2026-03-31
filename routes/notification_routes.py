from fastapi import APIRouter, Depends, HTTPException, Query
from general.security import Security
from services.notification_service import NotificationService, VaccinationNotificationService
from models.notification_model import NotificationResponse
from typing import List, Optional

router = APIRouter()

@router.get("/notifications")
async def get_notifications(
    unread_only: bool = Query(False, description="Get only unread notifications"),
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Get notifications for the current user.
    """
    try:
        user_id = current_user.get("user_id", current_user.get("username"))
        notifications = await NotificationService.get_user_notifications(user_id, unread_only)
        return {
            "notifications": notifications,
            "count": len(notifications)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get notifications: {str(e)}")

@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Mark a specific notification as read.
    """
    try:
        user_id = current_user.get("user_id", current_user.get("username"))
        return await NotificationService.mark_notification_read(notification_id, user_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark notification as read: {str(e)}")

@router.put("/notifications/read-all")
async def mark_all_notifications_read(current_user: dict = Depends(Security.get_current_user)):
    """
    Mark all notifications as read for the current user.
    """
    try:
        user_id = current_user.get("user_id", current_user.get("username"))
        return await NotificationService.mark_all_notifications_read(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark all notifications as read: {str(e)}")

@router.delete("/notifications/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: dict = Depends(Security.get_current_user)
):
    """
    Delete a specific notification.
    """
    try:
        user_id = current_user.get("user_id", current_user.get("username"))
        return await NotificationService.delete_notification(notification_id, user_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete notification: {str(e)}")

@router.post("/admin/check-vaccination-reminders")
async def check_vaccination_reminders(current_user: dict = Depends(Security.get_current_admin_user)):
    """
    Manually trigger vaccination reminder check (Admin only).
    This is useful for testing the background job.
    """
    try:
        return await VaccinationNotificationService.schedule_vaccination_reminders()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check vaccination reminders: {str(e)}")

@router.get("/notifications/unread-count")
async def get_unread_notifications_count(current_user: dict = Depends(Security.get_current_user)):
    """
    Get count of unread notifications for the current user.
    """
    try:
        user_id = current_user.get("user_id", current_user.get("username"))
        notifications = await NotificationService.get_user_notifications(user_id, unread_only=True)
        return {
            "unread_count": len(notifications)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get unread count: {str(e)}")
