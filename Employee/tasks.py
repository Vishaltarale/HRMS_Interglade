# attendance/tasks.py
from celery import shared_task
from datetime import time as dt_time
from utils.timezone_utils import now, today, current_time
from models import Employee, Attendance
import logging

logger = logging.getLogger(__name__)


@shared_task(name='attendance.tasks.create_daily_attendance_records')
def create_daily_attendance_records():
    """
    Create attendance records for all active employees at 12:01 AM
    """
    try:
        current_date = today()
        current_time = now()
        
        # Get all active employees with assigned shifts
        active_employees = Employee.objects.filter(
            status='active',
            shiftId__isnull=False
        )
        
        created_count = 0
        skipped_count = 0
        
        for employee in active_employees:
            # Check if attendance record already exists
            existing = Attendance.objects(
                employee=employee,
                date=current_date
            ).first()
            
            if not existing:
                # Create new attendance record
                attendance = Attendance(
                    employee=employee,
                    date=current_date,
                    status='pending',
                    created_at=current_time,
                    updated_at=current_time
                )
                attendance.save()
                created_count += 1
                logger.info(f"Created attendance for {employee.firstName} {employee.lastName}")
            else:
                skipped_count += 1
        
        message = f"Created {created_count} attendance records, skipped {skipped_count} existing"
        logger.info(message)
        return message
        
    except Exception as e:
        error_msg = f"Error creating daily attendance: {str(e)}"
        logger.error(error_msg)
        return error_msg


@shared_task(name='attendance.tasks.mark_absent_for_no_checkin')
def mark_absent_for_no_checkin():
    """
    Mark employees as absent who haven't checked in past cutoff time
    Runs at: 3:00 PM (morning), 10:00 PM (evening), 3:00 AM (night)
    """
    try:
        current_date = today()
        current_time_obj = current_time()
        current_datetime = now()
        
        # Shift-specific cutoff times
        SHIFT_CUTOFF_TIMES = {
            'morning': dt_time(15, 0),    # 3:00 PM
            'evening': dt_time(22, 0),    # 10:00 PM
            'night': dt_time(3, 0),       # 3:00 AM
            'general': dt_time(15, 0),    # Default 3:00 PM
        }
        
        marked_absent = 0
        
        # Get all pending attendance records without check-in
        pending_attendances = Attendance.objects(
            date=current_date,
            status='pending',
            check_in__exists=False
        )
        
        for attendance in pending_attendances:
            employee = attendance.employee
            
            if not employee.shiftId:
                continue
            
            shift = employee.shiftId
            shift_type = getattr(shift, 'shiftType', 'general').lower()
            cutoff_time = SHIFT_CUTOFF_TIMES.get(shift_type, SHIFT_CUTOFF_TIMES['general'])
            
            should_mark_absent = False
            
            # Handle night shift crossing midnight
            if shift_type == 'night' and current_time_obj.hour < 12:
                should_mark_absent = current_time_obj >= cutoff_time
            else:
                should_mark_absent = current_time_obj >= cutoff_time
            
            if should_mark_absent:
                attendance.status = 'absent'
                attendance.updated_at = current_datetime
                attendance.save()
                marked_absent += 1
                logger.warning(
                    f"Marked absent: {employee.firstName} {employee.lastName} "
                    f"({shift_type} shift, cutoff: {cutoff_time.strftime('%I:%M %p')})"
                )
        
        message = f"Marked {marked_absent} employees as absent"
        logger.info(message)
        return message
        
    except Exception as e:
        error_msg = f"Error marking absent: {str(e)}"
        logger.error(error_msg)
        return error_msg


@shared_task(name='attendance.tasks.test_task')
def test_task():
    """Simple test task to verify Celery is working"""
    logger.info("Test task executed successfully!")
    return "Test task completed"