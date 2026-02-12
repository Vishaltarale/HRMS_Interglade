# Employee/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.conf import settings
from utils.timezone_utils import (
    get_current_datetime_ist, get_current_date_ist, get_current_time_ist
)
from Employee.models import Employee, Attendance
from Employee.attendance_checker import (
    mark_absent_for_date, 
    check_and_mark_all_absent,
    manual_mark_absent_immediately
)
import pytz
import logging

logger = logging.getLogger(__name__)
scheduler = None


def create_attendance_records_job():
    """
    Create attendance records for all active employees at midnight
    Records are created with status='pending'
    """
    try:
        current_date_str = get_current_date_ist()
        current_datetime_str = get_current_datetime_ist()
        
        logger.info(f"🕛 Creating attendance records for {current_date_str}")
        
        active_employees = Employee.objects.filter(
            status='active',
            shiftId__ne=None,
            role__in=['JR_employee', 'SR_employee', 'hr']
        )
        
        created_count = 0
        
        for employee in active_employees:
            existing = Attendance.objects(
                employee=employee.id,
                date=current_date_str
            ).first()
            
            if not existing:
                Attendance(
                    employee=employee,
                    date=current_date_str,
                    status='pending',  # Always start as pending
                    created_at=current_datetime_str,
                    updated_at=current_datetime_str
                ).save()
                created_count += 1
                logger.info(f"✅ Created attendance for {employee.firstName} {employee.lastName}")
        
        logger.info(f"📊 Created {created_count} attendance records for {current_date_str}")
        
    except Exception as e:
        logger.error(f"❌ Error in create_attendance_records_job: {e}")
        import traceback
        traceback.print_exc()


def mark_absent_job():
    """
    Mark employees absent who haven't checked in by cutoff time
    This respects the grace period for newly created records
    """
    try:
        current_date_str = get_current_date_ist()
        logger.info(f"⏰ Running absent marking job for {current_date_str}")
        
        # Mark absent for today - will skip newly created records
        result = mark_absent_for_date(current_date_str, skip_new_records=True)
        
        if result.get('success'):
            logger.info(
                f"✅ Absent job complete: {result.get('marked_absent')} marked absent, "
                f"{result.get('skipped_new', 0)} skipped (new records)"
            )
        else:
            logger.error(f"⚠️ Absent job failed: {result.get('error')}")
        
    except Exception as e:
        logger.error(f"❌ Error in mark_absent_job: {e}")
        import traceback
        traceback.print_exc()


def end_of_day_absent_check():
    """
    Final absent check at end of day - marks ALL pending as absent
    This ignores grace periods since it's end of day
    Runs at 11:30 PM
    """
    try:
        current_date_str = get_current_date_ist()
        logger.info(f"🌙 Running END OF DAY absent check for {current_date_str}")
        
        # Force mark absent, ignoring grace periods
        result = manual_mark_absent_immediately(current_date_str)
        
        if result.get('success'):
            logger.info(
                f"✅ End of day check complete: {result.get('marked_absent')} marked absent"
            )
        else:
            logger.error(f"⚠️ End of day check failed: {result.get('error')}")
        
    except Exception as e:
        logger.error(f"❌ Error in end_of_day_absent_check: {e}")
        import traceback
        traceback.print_exc()


def comprehensive_absent_check_job():
    """
    Run comprehensive check for past 7 days
    This catches any missed absent markings if server was down
    Does NOT skip new records for past dates
    """
    try:
        logger.info("🔍 Running comprehensive absent check")
        
        result = check_and_mark_all_absent(days_back=7)
        
        if result.get('success'):
            logger.info(
                f"✅ Comprehensive check complete: {result.get('total_marked')} total marked"
            )
        else:
            logger.error(f"⚠️ Comprehensive check failed: {result.get('error')}")
        
    except Exception as e:
        logger.error(f"❌ Error in comprehensive_absent_check_job: {e}")
        import traceback
        traceback.print_exc()


def start_scheduler():
    """Start the APScheduler with all necessary jobs"""
    global scheduler
    
    if scheduler is not None:
        logger.info("Scheduler already running, skipping start")
        return
    
    logger.info("🚀 Starting attendance scheduler...")
    
    scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Kolkata'))
    
    # ============================================================================
    # Job 1: Create daily attendance records at 12:01 AM
    # ============================================================================
    scheduler.add_job(
        create_attendance_records_job,
        trigger=CronTrigger(hour=0, minute=1),
        id='create_daily_attendance',
        replace_existing=True,
        name='Create Daily Attendance Records'
    )
    logger.info("✅ Scheduled: Daily attendance creation at 12:01 AM")
    
    # ============================================================================
    # Job 2: Mark absent checks throughout the day
    # These check at strategic times to catch different shifts
    # ============================================================================
    
    # Check at 8:30 AM (for early morning shifts ending at 10:30 AM)
    scheduler.add_job(
        mark_absent_job,
        trigger=CronTrigger(hour=8, minute=30),
        id='mark_absent_0830',
        replace_existing=True,
        name='Mark Absent - 8:30 AM'
    )
    
    # Check at 11:00 AM (for morning shifts)
    scheduler.add_job(
        mark_absent_job,
        trigger=CronTrigger(hour=11, minute=0),
        id='mark_absent_1100',
        replace_existing=True,
        name='Mark Absent - 11:00 AM'
    )
    
    # Check at 2:00 PM (for afternoon shifts)
    scheduler.add_job(
        mark_absent_job,
        trigger=CronTrigger(hour=14, minute=0),
        id='mark_absent_1400',
        replace_existing=True,
        name='Mark Absent - 2:00 PM'
    )
    
    # Check at 4:00 PM (for day shifts 9-6, cutoff is 4:00 PM)
    scheduler.add_job(
        mark_absent_job,
        trigger=CronTrigger(hour=16, minute=0),
        id='mark_absent_1600',
        replace_existing=True,
        name='Mark Absent - 4:00 PM (Day Shift 9-6)'
    )
    
    # Check at 6:00 PM (for evening shifts)
    scheduler.add_job(
        mark_absent_job,
        trigger=CronTrigger(hour=18, minute=0),
        id='mark_absent_1800',
        replace_existing=True,
        name='Mark Absent - 6:00 PM'
    )
    
    # Check at 8:00 PM (for night shifts)
    scheduler.add_job(
        mark_absent_job,
        trigger=CronTrigger(hour=20, minute=0),
        id='mark_absent_2000',
        replace_existing=True,
        name='Mark Absent - 8:00 PM'
    )
    
    # Check at 10:00 PM (late evening shifts)
    scheduler.add_job(
        mark_absent_job,
        trigger=CronTrigger(hour=22, minute=0),
        id='mark_absent_2200',
        replace_existing=True,
        name='Mark Absent - 10:00 PM'
    )
    
    # Check at 3:00 AM (for night shifts that cross midnight)
    scheduler.add_job(
        mark_absent_job,
        trigger=CronTrigger(hour=3, minute=0),
        id='mark_absent_0300',
        replace_existing=True,
        name='Mark Absent - 3:00 AM (Night Shift)'
    )
    
    logger.info("✅ Scheduled: Absent marking at 8 intervals throughout the day")
    
    # ============================================================================
    # Job 3: END OF DAY - Final absent check at 11:30 PM
    # ============================================================================
    scheduler.add_job(
        end_of_day_absent_check,
        trigger=CronTrigger(hour=23, minute=30),
        id='end_of_day_absent',
        replace_existing=True,
        name='End of Day Absent Check - 11:30 PM'
    )
    logger.info("✅ Scheduled: End of day check at 11:30 PM (ignores grace period)")
    
    # ============================================================================
    # Job 4: Comprehensive check - runs every 6 hours
    # ============================================================================
    scheduler.add_job(
        comprehensive_absent_check_job,
        trigger=CronTrigger(hour='*/6'),  # Every 6 hours: 12 AM, 6 AM, 12 PM, 6 PM
        id='comprehensive_absent_check',
        replace_existing=True,
        name='Comprehensive Absent Check (Every 6 hours)'
    )
    logger.info("✅ Scheduled: Comprehensive check every 6 hours")
    
    # Start the scheduler
    scheduler.start()
    logger.info("🎯 Attendance scheduler started successfully!")
    
    # Log all scheduled jobs
    logger.info("\n📋 Scheduled Jobs Summary:")
    for job in scheduler.get_jobs():
        logger.info(f"  - {job.name} (ID: {job.id})")
        logger.info(f"    Next run: {job.next_run_time}")


def stop_scheduler():
    """Stop the scheduler gracefully"""
    global scheduler
    if scheduler is not None:
        scheduler.shutdown()
        scheduler = None
        logger.info("⏹️ Scheduler stopped")
    else:
        logger.info("Scheduler was not running")