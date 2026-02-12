# Employee/startup.py
from utils.timezone_utils import (
    get_current_datetime_ist, get_current_date_ist
)
from Employee.models import Employee, Attendance
from Employee.attendance_checker import check_and_mark_all_absent, mark_absent_for_date
import logging

logger = logging.getLogger(__name__)


def create_missing_attendance_records():
    """
    Check and create missing attendance records for today
    This runs automatically when server starts
    """
    try:
        current_date_str = get_current_date_ist()
        current_datetime_str = get_current_datetime_ist()
        
        logger.info(f"🔍 Checking for missing attendance records on {current_date_str}")
        
        # Get all active employees with assigned shifts
        active_employees = Employee.objects.filter(
            status='active',
            shiftId__ne=None,
            role__in=['JR_employee', 'SR_employee', 'hr']
        )
        
        created_count = 0
        existing_count = 0
        
        for employee in active_employees:
            # Check if attendance record exists for today
            existing = Attendance.objects(
                employee=employee,
                date=current_date_str
            ).first()
            
            if not existing:
                # Create new attendance record
                attendance = Attendance(
                    employee=employee,
                    date=current_date_str,
                    status='pending',
                    created_at=current_datetime_str,
                    updated_at=current_datetime_str
                )
                attendance.save()
                created_count += 1
                logger.info(f"✅ Created attendance for {employee.firstName} {employee.lastName}")
            else:
                existing_count += 1
        
        logger.info(
            f"📊 Attendance Summary: Created {created_count}, Found {existing_count} existing"
        )
        
        return {
            'success': True,
            'created': created_count,
            'existing': existing_count,
            'total_employees': active_employees.count(),
            'date': current_date_str
        }
        
    except Exception as e:
        logger.error(f"❌ Error creating attendance records: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }


def startup_absent_check():
    """
    Run comprehensive absent check on startup
    This handles cases where server was down and missed marking absents
    """
    try:
        logger.info("🔍 Running startup absent check...")
        
        # Check past 7 days for any missed absent markings
        result = check_and_mark_all_absent(days_back=7)
        
        if result.get('success'):
            logger.info(
                f"✅ Startup absent check complete: "
                f"{result.get('total_marked')} employees marked absent"
            )
        else:
            logger.error(f"⚠️ Startup absent check failed: {result.get('error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error in startup absent check: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }


def run_startup_tasks():
    """
    Run all startup tasks:
    1. Create missing attendance records for today
    2. Check and mark absent for past days (in case server was down)
    """
    try:
        logger.info("\n" + "="*70)
        logger.info("🚀 RUNNING ATTENDANCE STARTUP TASKS")
        logger.info("="*70)
        
        # Task 1: Create missing attendance records
        logger.info("\n📋 Task 1: Creating missing attendance records...")
        attendance_result = create_missing_attendance_records()
        
        if attendance_result.get('success'):
            logger.info(f"✅ Attendance creation complete")
            logger.info(f"   Created: {attendance_result.get('created')}")
            logger.info(f"   Existing: {attendance_result.get('existing')}")
        else:
            logger.error(f"⚠️ Attendance creation failed: {attendance_result.get('error')}")
        
        # Task 2: Check and mark absent for past days
        logger.info("\n🔍 Task 2: Checking for missed absent markings...")
        absent_result = startup_absent_check()
        
        if absent_result.get('success'):
            logger.info(f"✅ Absent check complete")
            logger.info(f"   Total marked: {absent_result.get('total_marked')}")
        else:
            logger.error(f"⚠️ Absent check failed: {absent_result.get('error')}")
        
        logger.info("\n" + "="*70)
        logger.info("✅ STARTUP TASKS COMPLETED")
        logger.info("="*70 + "\n")
        
        return {
            'success': True,
            'attendance_result': attendance_result,
            'absent_result': absent_result
        }
        
    except Exception as e:
        logger.error(f"❌ Error in startup tasks: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }