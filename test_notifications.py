#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from services.notification_service import NotificationService, VaccinationNotificationService
from models.notification_model import NotificationType

async def test_notification_system():
    try:
        print("=== TESTING NOTIFICATION SYSTEM ===")
        
        # Test 1: Create a test notification
        print("\n1. Creating test notification...")
        result = await NotificationService.create_notification(
            user_id="TEST_USER_001",
            message="Test vaccination reminder",
            notification_type=NotificationType.REMINDER,
            vaccination_record_id="test_record_001"
        )
        print(f"Notification created: {result}")
        
        # Test 2: Get notifications
        print("\n2. Getting notifications...")
        notifications = await NotificationService.get_user_notifications("TEST_USER_001")
        print(f"Found {len(notifications)} notifications")
        for notif in notifications:
            print(f"   - {notif.get('message', 'No message')}")
        
        # Test 3: Mark notification as read
        if notifications:
            notif_id = notifications[0].get("_id")
            print(f"\n3. Marking notification {notif_id} as read...")
            result = await NotificationService.mark_notification_read(notif_id, "TEST_USER_001")
            print(f"Result: {result}")
        
        # Test 4: Vaccination reminder check
        print("\n4. Testing vaccination reminder system...")
        result = await VaccinationNotificationService.schedule_vaccination_reminders()
        print(f"Reminder check result: {result}")
        
        print("\n=== ALL TESTS COMPLETED ===")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_notification_system())
