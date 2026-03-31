from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from services.notification_service import VaccinationNotificationService
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create scheduler instance
scheduler = AsyncIOScheduler()

def start_scheduler():
    """
    Start the background scheduler for vaccination notifications.
    """
    try:
        # Schedule vaccination reminder check to run daily at 9:00 AM
        scheduler.add_job(
            func=VaccinationNotificationService.schedule_vaccination_reminders,
            trigger=CronTrigger(hour=9, minute=0),  # Daily at 9:00 AM
            id="vaccination_reminder_check",
            name="Daily Vaccination Reminder Check",
            replace_existing=True,
            misfire_grace_time=3600  # 1 hour grace period
        )
        
        # Start the scheduler
        scheduler.start()
        logger.info("Vaccination notification scheduler started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")

def stop_scheduler():
    """
    Stop the background scheduler.
    """
    try:
        scheduler.shutdown()
        logger.info("Vaccination notification scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")

async def manual_vaccination_check():
    """
    Manually trigger vaccination check for testing purposes.
    """
    try:
        result = await VaccinationNotificationService.schedule_vaccination_reminders()
        logger.info(f"Manual vaccination check completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Manual vaccination check failed: {e}")
        raise e

# Add a job to run every hour for testing (can be removed in production)
def add_test_job():
    """
    Add a test job that runs every hour.
    Remove this in production.
    """
    scheduler.add_job(
        func=VaccinationNotificationService.schedule_vaccination_reminders,
        trigger=CronTrigger(minute=0),  # Every hour at minute 0
        id="test_vaccination_check",
        name="Test Vaccination Check (Hourly)",
        replace_existing=True,
        misfire_grace_time=300  # 5 minute grace period
    )
    logger.info("Test vaccination check job added (runs hourly)")
