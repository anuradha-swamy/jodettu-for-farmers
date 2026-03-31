# Vaccination Notification System Documentation

## Overview
A comprehensive vaccination notification system that automatically reminds users about upcoming and overdue vaccinations for their animals.

## Features

### 1. Vaccination Records
- Each animal can have multiple vaccination records
- Each vaccination includes:
  - `vaccination_name`: Name of the vaccine
  - `next_vaccination_date`: Date for next dose (ISO format)
  - `vaccination_status`: "pending" or "completed"

### 2. Notification Types
- **Reminder Notifications**: Sent 10 days before vaccination date
- **Due Notifications**: Sent when vaccination date has passed and status is still "pending"

### 3. Background Scheduler
- Runs daily at 9:00 AM
- Automatically checks all animals for upcoming/overdue vaccinations
- Creates appropriate notifications

### 4. Notification Management
- View notifications (all or unread only)
- Mark notifications as read
- Delete notifications
- Get unread count

## API Endpoints

### Notifications
- `GET /Jodettu/Notifications/notifications` - Get user notifications
- `PUT /Jodettu/Notifications/notifications/{id}/read` - Mark notification as read
- `PUT /Jodettu/Notifications/notifications/read-all` - Mark all as read
- `DELETE /Jodettu/Notifications/notifications/{id}` - Delete notification
- `GET /Jodettu/Notifications/notifications/unread-count` - Get unread count

### Admin
- `POST /Jodettu/Notifications/admin/check-vaccination-reminders` - Manual trigger (admin only)

### Animal Details (Enhanced)
- `GET /Jodettu/Animals/animal/{animal_id}` - Now includes vaccination status

## Installation

1. Install APScheduler:
```bash
pip install apscheduler>=3.10.0
```

2. Restart your FastAPI server

## Usage Examples

### Adding Animal with Vaccinations
```json
{
  "own_animal_name": "Bessie",
  "own_animal_type": "cow",
  "own_animal_breed": "Holstein",
  "own_animal_age": 3,
  "vaccinations": [
    {
      "vaccination_name": "Rabies Vaccine",
      "next_vaccination_date": "2024-06-15T10:30:00",
      "vaccination_status": "pending"
    },
    {
      "vaccination_name": "Foot & Mouth Disease",
      "next_vaccination_date": "2024-08-20T10:30:00",
      "vaccination_status": "pending"
    }
  ]
}
```

### Getting Notifications
```bash
curl -X 'GET' \
  'http://localhost:8000/Jodettu/Notifications/notifications' \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

### Response Format
```json
{
  "notifications": [
    {
      "_id": "64f8a1b2c3d4e5f6a7b8c9d0",
      "user_id": "USER_0001",
      "message": "Reminder: Bessie's Rabies Vaccine vaccination is due in 5 days on 2024-06-15",
      "type": "reminder",
      "created_at": "2024-06-05T09:00:00Z",
      "is_read": false,
      "vaccination_record_id": "OWN_01_Rabies Vaccine_2024-06-15"
    }
  ],
  "count": 1
}
```

## Database Schema

### Notifications Collection
```javascript
{
  "_id": ObjectId,
  "user_id": "USER_0001",
  "message": "Reminder notification text",
  "type": "reminder" | "due",
  "created_at": ISODate,
  "is_read": false,
  "vaccination_record_id": "animal_id_vaccine_name_date"
}
```

### Animals Collection (Enhanced)
```javascript
{
  "own_animal_id": "OWN_01",
  "vaccinations": [
    {
      "vaccination_name": "Rabies Vaccine",
      "next_vaccination_date": ISODate,
      "vaccination_status": "pending" | "completed"
    }
  ]
}
```

## Configuration

### Scheduler Settings
- **Daily Check**: 9:00 AM UTC
- **Reminder Period**: 10 days before due date
- **Grace Period**: 1 hour for missed runs

### Customization
You can modify the scheduler settings in `services/scheduler_service.py`:
- Change check time: Modify `CronTrigger(hour=9, minute=0)`
- Change reminder days: Modify `reminder_date = today + timedelta(days=10)`
- Add test jobs: Call `add_test_job()` for hourly checks

## Monitoring

### Logs
The system logs all scheduler activities:
- Scheduler start/stop
- Notification creation
- Error handling

### Manual Testing
Use the admin endpoint to manually trigger checks:
```bash
curl -X 'POST' \
  'http://localhost:8000/Jodettu/Notifications/admin/check-vaccination-reminders' \
  -H 'Authorization: Bearer ADMIN_TOKEN'
```

## Troubleshooting

### Common Issues
1. **Scheduler not starting**: Check APScheduler installation
2. **No notifications**: Verify animals have vaccination records with future dates
3. **Duplicate notifications**: System prevents duplicates using vaccination_record_id

### Debug Mode
Enable test job in `scheduler_service.py` for hourly checks during development.

## Security
- All notification endpoints require authentication
- Admin-only endpoints for manual triggers
- User isolation: Users can only access their own notifications
