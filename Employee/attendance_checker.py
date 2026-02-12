# Employee/attendance_checker.py
from utils.timezone_utils import (
    get_current_datetime_ist, get_current_date_ist, get_current_time_ist,
    is_time_after, calculate_work_hours, is_valid_time_format
)
from Employee.models import Employee, Attendance
from Shifts.models import Shift
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def get_shift_absent_cutoff_time(shift):
    """
    Calculate the cutoff time for marking absent based on shift
    Returns: time string "HH:MM:SS" for the cutoff (shift end time - 2 hours)
    
    Args:
        shift: Shift object with string time fields
    
    Returns: string "HH:MM:SS" or None
    """
    if not shift or not shift.endTime:
        return None
    
    try:
        # Parse shift end time string "HH:MM:SS"
        end_time = datetime.strptime(shift.endTime, "%H:%M:%S")
        
        # Subtract 2 hours
        cutoff_time = end_time - timedelta(hours=2)
        
        # Return as string
        return cutoff_time.strftime("%H:%M:%S")
    except Exception as e:
        logger.error(f"Error calculating cutoff time: {e}")
        return None


def should_mark_absent_for_shift(shift, current_time_str, current_date_str):
    """
    Determine if we should mark absent based on shift timing
    
    RULE: Mark absent ONLY when current time >= (shift end time - 2 hours)
    Never mark absent before this cutoff time.
    
    Args:
        shift: Shift object
        current_time_str: current time string "HH:MM:SS"
        current_date_str: current date string "YYYY-MM-DD"
        
    Returns: Boolean
    """
    if not shift:
        return False
    
    cutoff_time = get_shift_absent_cutoff_time(shift)
    if not cutoff_time:
        return False
    
    shift_type = getattr(shift, 'shiftType', '').lower()
    
    try:
        # Parse current time for hour checking
        current_time_obj = datetime.strptime(current_time_str, "%H:%M:%S").time()
        
        # CRITICAL: Only mark absent if current time has reached or passed the cutoff
        # This ensures we DON'T mark absent before (shift_end - 2 hours)
        
        # Handle night shift that crosses midnight
        if shift_type == 'night':
            # Parse shift times
            shift_end = datetime.strptime(shift.endTime, "%H:%M:%S").time()
            shift_start = datetime.strptime(shift.fromTime, "%H:%M:%S").time()
            
            # If end time is less than start time, shift crosses midnight
            if shift_end < shift_start:
                # For night shifts crossing midnight
                # Example: 10 PM - 6 AM, cutoff = 4 AM
                cutoff_obj = datetime.strptime(cutoff_time, "%H:%M:%S").time()
                
                # If cutoff is in early morning (e.g., 4 AM)
                if cutoff_obj.hour < 12:
                    # Current time must be after midnight and >= cutoff
                    if current_time_obj.hour < 12:
                        return is_time_after(current_time_str, cutoff_time)
                    else:
                        # Still in previous day (PM), not yet at cutoff
                        return False
                else:
                    # Cutoff is in evening
                    return is_time_after(current_time_str, cutoff_time)
        
        # For all other shifts (day, afternoon, rotational)
        # Simple comparison: current_time >= cutoff_time
        result = is_time_after(current_time_str, cutoff_time)
        
        logger.debug(
            f"Shift: {shift_type}, Current: {current_time_str}, "
            f"Cutoff: {cutoff_time}, Should mark: {result}"
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error in should_mark_absent_for_shift: {e}")
        return False


def is_attendance_record_new(attendance, grace_minutes=30):
    """
    Check if attendance record was just created (within grace period)
    This prevents marking newly created records as absent immediately
    
    Args:
        attendance: Attendance object
        grace_minutes: Grace period in minutes (default: 30)
        
    Returns: Boolean - True if record is newly created
    """
    if not attendance.created_at:
        return False
    
    try:
        # Parse created_at string "YYYY-MM-DD HH:MM:SS"
        created_dt = datetime.strptime(attendance.created_at, "%Y-%m-%d %H:%M:%S")
        
        # Get current datetime
        current_datetime_str = get_current_datetime_ist()
        current_dt = datetime.strptime(current_datetime_str, "%Y-%m-%d %H:%M:%S")
        
        # Calculate time difference
        time_since_creation = current_dt - created_dt
        
        # If created within grace_minutes, consider it new
        return time_since_creation.total_seconds() < (grace_minutes * 60)
    
    except Exception as e:
        logger.error(f"Error checking if record is new: {e}")
        return False


def mark_absent_for_date(check_date_str, skip_new_records=True):
    """
    Mark employees absent for a specific date if they haven't checked in
    and the cutoff time has passed
    
    Args:
        check_date_str: date string "YYYY-MM-DD" to check
        skip_new_records: Skip newly created records (default: True)
        
    Returns: dict with results
    """
    try:
        current_datetime_str = get_current_datetime_ist()
        current_time_str = get_current_time_ist()
        current_date_str = get_current_date_ist()
        
        logger.info(f"🔍 Checking absent status for date: {check_date_str}")
        
        # Get all pending attendance records for this date
        pending_attendances = Attendance.objects.filter(
            date=check_date_str,
            status='pending'
        )
        
        marked_absent = 0
        skipped = 0
        skipped_new = 0
        
        for attendance in pending_attendances:
            # Skip if already checked in
            if attendance.check_in_time:
                logger.debug(f"Skipping {attendance.employee.firstName} - already checked in")
                continue
            
            employee = attendance.employee
            
            if not employee or not employee.shiftId:
                skipped += 1
                logger.warning(f"Skipping employee {employee.id if employee else 'Unknown'} - no shift assigned")
                continue
            
            # Skip newly created records to prevent immediate absent marking
            if skip_new_records and check_date_str == current_date_str:
                if is_attendance_record_new(attendance, grace_minutes=30):
                    skipped_new += 1
                    logger.debug(
                        f"⏳ Skipping {employee.firstName} {employee.lastName} - "
                        f"record created recently (within grace period)"
                    )
                    continue
            
            shift = employee.shiftId
            should_mark = False
            
            # If checking for today, use real-time cutoff logic
            if check_date_str == current_date_str:
                should_mark = should_mark_absent_for_shift(
                    shift, 
                    current_time_str, 
                    current_date_str
                )
                
                if should_mark:
                    logger.info(
                        f"⏰ Cutoff passed for {employee.firstName} {employee.lastName} "
                        f"(Shift: {shift.shiftType}, Cutoff: {get_shift_absent_cutoff_time(shift)})"
                    )
                else:
                    logger.debug(
                        f"⏳ Cutoff NOT passed yet for {employee.firstName} {employee.lastName} "
                        f"(Cutoff: {get_shift_absent_cutoff_time(shift)})"
                    )
            else:
                # For past dates, always mark as absent if not checked in
                # Compare date strings directly
                should_mark = check_date_str < current_date_str
                if should_mark:
                    logger.info(f"📅 Past date - marking {employee.firstName} {employee.lastName} as absent")
            
            if should_mark:
                attendance.status = 'absent'
                attendance.updated_at = current_datetime_str
                attendance.save()
                marked_absent += 1
                
                logger.info(
                    f"✅ Marked {employee.firstName} {employee.lastName} as ABSENT "
                    f"for {check_date_str} (Shift: {shift.shiftType}, "
                    f"Cutoff: {get_shift_absent_cutoff_time(shift)}, "
                    f"Current: {current_time_str if check_date_str == current_date_str else 'Past date'})"
                )
        
        logger.info(
            f"📊 Absent marking complete for {check_date_str}: "
            f"{marked_absent} marked absent, {skipped} skipped (no shift), "
            f"{skipped_new} skipped (newly created)"
        )
        
        return {
            'success': True,
            'marked_absent': marked_absent,
            'skipped': skipped,
            'skipped_new': skipped_new,
            'date': check_date_str
        }
        
    except Exception as e:
        logger.error(f"❌ Error marking absent for {check_date_str}: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e),
            'date': check_date_str
        }


def check_and_mark_all_absent(days_back=7):
    """
    Check and mark absent for today and past days
    This handles cases where server was down during cutoff times
    
    Args:
        days_back: Number of days to check backwards (default: 7)
        
    Returns: dict with complete results
    """
    try:
        current_date_str = get_current_date_ist()
        results = []
        total_marked = 0
        
        logger.info(f"🔍 Running comprehensive absent check for {days_back} days")
        
        # Check each day from today going back
        for i in range(days_back + 1):
            # Calculate check date by subtracting days
            check_date = datetime.strptime(current_date_str, "%Y-%m-%d").date()
            check_date = check_date - timedelta(days=i)
            check_date_str = check_date.strftime("%Y-%m-%d")
            
            # For today, skip new records. For past dates, don't skip
            skip_new = (check_date_str == current_date_str)
            result = mark_absent_for_date(check_date_str, skip_new_records=skip_new)
            results.append(result)
            
            if result.get('success'):
                total_marked += result.get('marked_absent', 0)
        
        logger.info(f"📊 Comprehensive check complete: {total_marked} total marked absent")
        
        return {
            'success': True,
            'total_marked': total_marked,
            'daily_results': results
        }
        
    except Exception as e:
        logger.error(f"❌ Error in comprehensive absent check: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def get_employees_to_check_now():
    """
    Get list of employees whose shift cutoff time has passed right now
    Useful for immediate checking and debugging
    
    Returns: List of tuples (Attendance, cutoff_time, reason)
    """
    try:
        current_date_str = get_current_date_ist()
        current_time_str = get_current_time_ist()
        
        # Get all pending attendances for today without check_in
        pending_attendances = Attendance.objects.filter(
            date=current_date_str,
            status='pending'
        )
        
        to_mark = []
        
        for attendance in pending_attendances:
            # Skip if checked in
            if attendance.check_in_time:
                continue
                
            employee = attendance.employee
            
            if not employee or not employee.shiftId:
                continue
            
            # Skip newly created records
            if is_attendance_record_new(attendance, grace_minutes=30):
                continue
            
            shift = employee.shiftId
            cutoff_time = get_shift_absent_cutoff_time(shift)
            
            if should_mark_absent_for_shift(shift, current_time_str, current_date_str):
                to_mark.append((
                    attendance,
                    cutoff_time,
                    f"Shift: {shift.shiftType}, Cutoff: {cutoff_time}, Current: {current_time_str}"
                ))
        
        return to_mark
        
    except Exception as e:
        logger.error(f"❌ Error getting employees to check: {str(e)}")
        return []


def manual_mark_absent_immediately(check_date_str=None):
    """
    FORCE mark absent for a date, ignoring grace periods
    Use this for manual corrections or end-of-day processing
    
    Args:
        check_date_str: date string "YYYY-MM-DD" to check (default: today)
        
    Returns: dict with results
    """
    if check_date_str is None:
        check_date_str = get_current_date_ist()
    
    logger.info(f"🔨 FORCE marking absent for {check_date_str} (ignoring grace periods)")
    
    # Call mark_absent_for_date with skip_new_records=False
    return mark_absent_for_date(check_date_str, skip_new_records=False)