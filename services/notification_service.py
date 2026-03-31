from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import HTTPException
from general.database import notifications_collection, own_animals
from models.notification_model import Notification, NotificationType, VaccinationRecord, VaccinationStatus
from bson import ObjectId
import uuid

class NotificationService:
    
    @staticmethod
    async def create_notification(user_id: str, message: str, notification_type: NotificationType, vaccination_record_id: Optional[str] = None) -> dict:
        """
        Create a new notification.
        """
        notification_data = {
            "user_id": user_id,
            "message": message,
            "type": notification_type.value,
            "created_at": datetime.utcnow(),
            "is_read": False,
            "vaccination_record_id": vaccination_record_id
        }
        
        result = notifications_collection.insert_one(notification_data)
        notification_data["_id"] = str(result.inserted_id)
        
        return {
            "message": "Notification created successfully",
            "notification_id": str(result.inserted_id)
        }
    
    @staticmethod
    async def get_user_notifications(user_id: str, unread_only: bool = False) -> List[dict]:
        """
        Get notifications for a user.
        """
        query = {"user_id": user_id}
        if unread_only:
            query["is_read"] = False
        
        notifications = list(notifications_collection.find(query).sort("created_at", -1))
        
        for notification in notifications:
            notification["_id"] = str(notification["_id"])
        
        return notifications
    
    @staticmethod
    async def mark_notification_read(notification_id: str, user_id: str) -> dict:
        """
        Mark a notification as read.
        """
        result = notifications_collection.update_one(
            {"_id": ObjectId(notification_id), "user_id": user_id},
            {"$set": {"is_read": True, "read_at": datetime.utcnow()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Notification not found or already read")
        
        return {"message": "Notification marked as read"}
    
    @staticmethod
    async def mark_all_notifications_read(user_id: str) -> dict:
        """
        Mark all notifications as read for a user.
        """
        result = notifications_collection.update_many(
            {"user_id": user_id, "is_read": False},
            {"$set": {"is_read": True, "read_at": datetime.utcnow()}}
        )
        
        return {
            "message": f"Marked {result.modified_count} notifications as read",
            "count": result.modified_count
        }
    
    @staticmethod
    async def delete_notification(notification_id: str, user_id: str) -> dict:
        """
        Delete a notification.
        """
        result = notifications_collection.delete_one({
            "_id": ObjectId(notification_id),
            "user_id": user_id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"message": "Notification deleted successfully"}

class VaccinationNotificationService:
    
    @staticmethod
    async def schedule_vaccination_reminders():
        """
        Background job to check and send vaccination reminders.
        This should be called daily by the scheduler.
        """
        today = datetime.utcnow()
        reminder_date = today + timedelta(days=10)
        
        # Get all animals with upcoming vaccinations
        animals = list(own_animals.find({
            "function": {"$ne": "ID_counter"}
        }))
        
        notifications_created = 0
        
        for animal in animals:
            user_id = animal.get("user_id")
            animal_id = animal.get("own_animal_id")
            animal_name = animal.get("own_animal_name", "Unknown")
            
            if not user_id or not animal_id:
                continue
            
            # Check for upcoming vaccinations (within 10 days)
            vaccinations = animal.get("vaccinations", [])
            for vacc in vaccinations:
                if isinstance(vacc, dict):
                    next_date = vacc.get("next_vaccination_date")
                    vacc_name = vacc.get("vaccination_name", "Unknown Vaccine")
                    
                    if next_date:
                        try:
                            # Parse the date if it's a string
                            if isinstance(next_date, str):
                                next_date = datetime.fromisoformat(next_date.replace('Z', '+00:00'))
                            
                            # Check if vaccination is within reminder period
                            if today <= next_date <= reminder_date:
                                days_until = (next_date - today).days
                                
                                # Check if reminder already exists
                                existing_notification = notifications_collection.find_one({
                                    "user_id": user_id,
                                    "vaccination_record_id": f"{animal_id}_{vacc_name}_{next_date.strftime('%Y-%m-%d')}",
                                    "type": "reminder"
                                })
                                
                                if not existing_notification:
                                    message = f"Reminder: {animal_name}'s {vacc_name} vaccination is due in {days_until} days on {next_date.strftime('%Y-%m-%d')}"
                                    
                                    await NotificationService.create_notification(
                                        user_id=user_id,
                                        message=message,
                                        notification_type=NotificationType.REMINDER,
                                        vaccination_record_id=f"{animal_id}_{vacc_name}_{next_date.strftime('%Y-%m-%d')}"
                                    )
                                    notifications_created += 1
                            
                            # Check if vaccination is overdue
                            elif next_date < today:
                                # Check if due notification already exists
                                existing_notification = notifications_collection.find_one({
                                    "user_id": user_id,
                                    "vaccination_record_id": f"{animal_id}_{vacc_name}_{next_date.strftime('%Y-%m-%d')}",
                                    "type": "due"
                                })
                                
                                if not existing_notification:
                                    days_overdue = (today - next_date).days
                                    message = f"URGENT: {animal_name}'s {vacc_name} vaccination was due {days_overdue} days ago! Please schedule vaccination immediately."
                                    
                                    await NotificationService.create_notification(
                                        user_id=user_id,
                                        message=message,
                                        notification_type=NotificationType.DUE,
                                        vaccination_record_id=f"{animal_id}_{vacc_name}_{next_date.strftime('%Y-%m-%d')}"
                                    )
                                    notifications_created += 1
                                    
                        except Exception as e:
                            print(f"Error processing vaccination for animal {animal_id}: {e}")
                            continue
        
        return {
            "message": f"Vaccination reminder check completed",
            "notifications_created": notifications_created,
            "animals_processed": len(animals)
        }
