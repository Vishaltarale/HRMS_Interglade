# your_project/celery.py
import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')

app = Celery('your_project')

# Load config from Django settings with CELERY namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()

# Celery Beat Schedule - Automated Tasks
app.conf.beat_schedule = {
    # Create attendance records daily at 12:01 AM
    'create-daily-attendance-records': {
        'task': 'attendance.tasks.create_daily_attendance_records',
        'schedule': crontab(hour=0, minute=1),  # 12:01 AM
    },
    
    # Mark absent for morning shift at 3:00 PM
    'mark-absent-morning-shift': {
        'task': 'attendance.tasks.mark_absent_for_no_checkin',
        'schedule': crontab(hour=15, minute=0),  # 3:00 PM
    },
    
    # Mark absent for evening shift at 10:00 PM
    'mark-absent-evening-shift': {
        'task': 'attendance.tasks.mark_absent_for_no_checkin',
        'schedule': crontab(hour=22, minute=0),  # 10:00 PM
    },
    
    # Mark absent for night shift at 3:00 AM
    'mark-absent-night-shift': {
        'task': 'attendance.tasks.mark_absent_for_no_checkin',
        'schedule': crontab(hour=3, minute=0),  # 3:00 AM
    },
}

# Set timezone
app.conf.timezone = 'Asia/Kolkata'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')