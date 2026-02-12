from datetime import datetime, timedelta

def is_holiday(date_str, employee=None):
    """
    Check if a given date is a holiday
    Args:
        date_str: Date in "YYYY-MM-DD" format
        employee: Employee object (optional, for department/location specific holidays)
    Returns:
        tuple: (is_holiday, holiday_object or None)
    """
    try:
        from Leave.models import Holiday
        
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        year = date_obj.year
        
        holiday = Holiday.objects(
            date=date_str,
            year=year,
            is_active=True
        ).first()
        
        if not holiday:
            return False, None
        
        # Check if applicable to employee
        if employee and not holiday.is_applicable_to_employee(employee):
            return False, None
        
        return True, holiday
    
    except Exception as e:
        print(f"Error checking holiday: {e}")
        return False, None


def get_working_days(start_date_str, end_date_str, employee=None, exclude_weekends=True):
    """
    Calculate working days between two dates excluding holidays and weekends
    Args:
        start_date_str: Start date in "YYYY-MM-DD" format
        end_date_str: End date in "YYYY-MM-DD" format
        employee: Employee object (optional)
        exclude_weekends: Whether to exclude Sat/Sun (default: True)
    Returns:
        int: Number of working days
    """
    try:
        start = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        
        working_days = 0
        current = start
        
        while current <= end:
            # Skip weekends (Saturday=5, Sunday=6)
            if exclude_weekends and current.weekday() >= 5:
                current += timedelta(days=1)
                continue
            
            # Check if it's a holiday
            is_hol, _ = is_holiday(current.strftime("%Y-%m-%d"), employee)
            if not is_hol:
                working_days += 1
            
            current += timedelta(days=1)
        
        return working_days
    
    except Exception as e:
        print(f"Error calculating working days: {e}")
        # Fallback to simple day count
        try:
            start = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            return (end - start).days + 1
        except:
            return 1


def get_holidays_in_range(start_date_str, end_date_str, employee=None):
    """
    Get all holidays within a date range
    Args:
        start_date_str: Start date in "YYYY-MM-DD" format
        end_date_str: End date in "YYYY-MM-DD" format
        employee: Employee object (optional)
    Returns:
        list: List of Holiday objects in the date range
    """
    try:
        from Leave.models import Holiday
        
        start = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        
        # Get years in range
        years = list(range(start.year, end.year + 1))
        
        holidays_in_range = []
        
        for year in years:
            holidays = Holiday.objects(year=year, is_active=True)
            
            for holiday in holidays:
                holiday_date = datetime.strptime(holiday.date, "%Y-%m-%d").date()
                
                if start <= holiday_date <= end:
                    # Check if applicable to employee
                    if employee:
                        if holiday.is_applicable_to_employee(employee):
                            holidays_in_range.append(holiday)
                    else:
                        holidays_in_range.append(holiday)
        
        return sorted(holidays_in_range, key=lambda h: h.date)
    
    except Exception as e:
        print(f"Error getting holidays in range: {e}")
        return []


def is_weekend(date_str):
    """
    Check if a date is a weekend (Saturday or Sunday)
    Args:
        date_str: Date in "YYYY-MM-DD" format
    Returns:
        bool: True if weekend, False otherwise
    """
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        # weekday(): Monday=0, Sunday=6
        return date_obj.weekday() >= 5
    except:
        return False


def validate_leave_dates(start_date_str, end_date_str, employee=None):
    """
    Validate leave request dates and provide warnings
    Args:
        start_date_str: Start date in "YYYY-MM-DD" format
        end_date_str: End date in "YYYY-MM-DD" format
        employee: Employee object (optional)
    Returns:
        dict: Validation result with warnings
    """
    result = {
        'is_valid': True,
        'warnings': [],
        'working_days': 0,
        'total_days': 0,
        'holidays_count': 0,
        'weekend_count': 0,
        'holidays': []
    }
    
    try:
        start = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        
        # Calculate total days
        result['total_days'] = (end - start).days + 1
        
        # Get holidays in range
        holidays = get_holidays_in_range(start_date_str, end_date_str, employee)
        result['holidays'] = [
            {'name': h.name, 'date': h.date, 'type': h.holiday_type} 
            for h in holidays
        ]
        result['holidays_count'] = len(holidays)
        
        # Calculate working days
        result['working_days'] = get_working_days(start_date_str, end_date_str, employee)
        
        # Calculate weekends
        current = start
        weekend_count = 0
        while current <= end:
            if current.weekday() >= 5:
                weekend_count += 1
            current += timedelta(days=1)
        result['weekend_count'] = weekend_count
        
        # Add warnings
        if result['holidays_count'] > 0:
            result['warnings'].append(
                f"Your leave includes {result['holidays_count']} holiday(s). "
                f"These won't be deducted from your balance."
            )
        
        if result['weekend_count'] > 0:
            result['warnings'].append(
                f"Your leave includes {result['weekend_count']} weekend day(s)."
            )
        
        if result['working_days'] == 0:
            result['warnings'].append(
                "All selected days are holidays/weekends. No leave balance will be deducted."
            )
        
        # Check if starting on weekend
        if is_weekend(start_date_str):
            result['warnings'].append("Your leave starts on a weekend.")
        
        # Check if ending on weekend
        if is_weekend(end_date_str):
            result['warnings'].append("Your leave ends on a weekend.")
        
    except Exception as e:
        result['is_valid'] = False
        result['warnings'].append(f"Error validating dates: {str(e)}")
    
    return result


def get_upcoming_holidays(employee, days=30):
    """
    Get upcoming holidays for an employee
    Args:
        employee: Employee object
        days: Number of days to look ahead
    Returns:
        list: List of upcoming holidays
    """
    from utils.timezone_utils import get_current_date_ist
    from Leave.models import Holiday
    
    try:
        today = get_current_date_ist()
        today_obj = datetime.strptime(today, "%Y-%m-%d").date()
        future_date = today_obj + timedelta(days=days)
        
        holidays = Holiday.objects(
            year=today_obj.year,
            is_active=True
        )
        
        upcoming = []
        for holiday in holidays:
            holiday_date = datetime.strptime(holiday.date, "%Y-%m-%d").date()
            if today_obj <= holiday_date <= future_date:
                if holiday.is_applicable_to_employee(employee):
                    upcoming.append(holiday)
        
        return sorted(upcoming, key=lambda h: h.date)
    
    except Exception as e:
        print(f"Error getting upcoming holidays: {e}")
        return []


def get_holiday_count_for_year(employee, year=None):
    """
    Get total number of holidays for an employee in a year
    """
    from Leave.models import Holiday
    
    if not year:
        year = datetime.utcnow().year
    
    holidays = Holiday.objects(year=year, is_active=True)
    
    count = 0
    for holiday in holidays:
        if holiday.is_applicable_to_employee(employee):
            count += 1
    
    return count
