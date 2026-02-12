import pytz
from datetime import datetime, date, time as dt_time, timedelta

# Define Kolkata timezone as a constant
KOLKATA_TZ = pytz.timezone('Asia/Kolkata')

# Date format: "YYYY-MM-DD"
DATE_FORMAT = "%Y-%m-%d"

# Time format: "HH:MM:SS" (24-hour)
TIME_FORMAT = "%H:%M:%S"

# DateTime format: "YYYY-MM-DD HH:MM:SS"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# Display formats
DISPLAY_DATE_FORMAT = "%d-%m-%Y"  # DD-MM-YYYY
DISPLAY_TIME_12HR_FORMAT = "%I:%M:%S %p"  # 12-hour with AM/PM
DISPLAY_DATETIME_FORMAT = "%d-%m-%Y %I:%M:%S %p"  # Full display


# ============================================================================
# CURRENT TIME FUNCTIONS (Returns IST as strings)
# ============================================================================

def get_current_datetime_ist():
    """
    Get current datetime in IST as string
    Returns: string in format "YYYY-MM-DD HH:MM:SS"
    """
    now = datetime.now(KOLKATA_TZ)
    return now.strftime(DATETIME_FORMAT)


def get_current_date_ist():
    """
    Get current date in IST as string
    Returns: string in format "YYYY-MM-DD"
    """
    now = datetime.now(KOLKATA_TZ)
    return now.strftime(DATE_FORMAT)


def get_current_time_ist():
    """
    Get current time in IST as string
    Returns: string in format "HH:MM:SS"
    """
    now = datetime.now(KOLKATA_TZ)
    return now.strftime(TIME_FORMAT)


# ============================================================================
# FORMATTING FUNCTIONS (For display purposes)
# ============================================================================

def format_date_display(date_str):
    """
    Format date string from "YYYY-MM-DD" to "DD-MM-YYYY"
    Args:
        date_str: date string in "YYYY-MM-DD" format
    Returns: formatted date string "DD-MM-YYYY"
    """
    if not date_str:
        return None
    try:
        dt = datetime.strptime(date_str, DATE_FORMAT)
        return dt.strftime(DISPLAY_DATE_FORMAT)
    except:
        return date_str


def format_time_display(time_str):
    """
    Format time string from "HH:MM:SS" to "HH:MM:SS AM/PM"
    Args:
        time_str: time string in "HH:MM:SS" format (24-hour)
    Returns: formatted time string in 12-hour format with AM/PM
    """
    if not time_str:
        return None
    try:
        dt = datetime.strptime(time_str, TIME_FORMAT)
        return dt.strftime(DISPLAY_TIME_12HR_FORMAT)
    except:
        return time_str


def format_datetime_display(datetime_str):
    """
    Format datetime string to display format
    Args:
        datetime_str: datetime string in "YYYY-MM-DD HH:MM:SS" format
    Returns: formatted datetime string "DD-MM-YYYY HH:MM:SS AM/PM"
    """
    if not datetime_str:
        return None
    try:
        dt = datetime.strptime(datetime_str, DATETIME_FORMAT)
        return dt.strftime(DISPLAY_DATETIME_FORMAT)
    except:
        return datetime_str


# ============================================================================
# TIME COMPARISON FUNCTIONS
# ============================================================================

def is_time_after(time1_str, time2_str):
    """
    Check if time1 is after time2
    Args:
        time1_str: time string "HH:MM:SS"
        time2_str: time string "HH:MM:SS"
    Returns: boolean
    """
    if not time1_str or not time2_str:
        return False
    try:
        t1 = datetime.strptime(time1_str, TIME_FORMAT).time()
        t2 = datetime.strptime(time2_str, TIME_FORMAT).time()
        return t1 > t2
    except:
        return False


def is_time_before(time1_str, time2_str):
    """
    Check if time1 is before time2
    Args:
        time1_str: time string "HH:MM:SS"
        time2_str: time string "HH:MM:SS"
    Returns: boolean
    """
    if not time1_str or not time2_str:
        return False
    try:
        t1 = datetime.strptime(time1_str, TIME_FORMAT).time()
        t2 = datetime.strptime(time2_str, TIME_FORMAT).time()
        return t1 < t2
    except:
        return False


def compare_dates(date1_str, date2_str):
    """
    Compare two date strings
    Args:
        date1_str: date string "YYYY-MM-DD"
        date2_str: date string "YYYY-MM-DD"
    Returns: -1 if date1 < date2, 0 if equal, 1 if date1 > date2
    """
    if not date1_str or not date2_str:
        return 0
    try:
        d1 = datetime.strptime(date1_str, DATE_FORMAT).date()
        d2 = datetime.strptime(date2_str, DATE_FORMAT).date()
        if d1 < d2:
            return -1
        elif d1 > d2:
            return 1
        return 0
    except:
        return 0


# ============================================================================
# DATE RANGE FUNCTIONS
# ============================================================================

def get_date_range(start_date_str, end_date_str):
    """
    Generate list of dates between start and end (inclusive)
    Args:
        start_date_str: start date "YYYY-MM-DD"
        end_date_str: end date "YYYY-MM-DD"
    Returns: list of date strings in "YYYY-MM-DD" format
    """
    if not start_date_str or not end_date_str:
        return []
    
    try:
        start_date = datetime.strptime(start_date_str, DATE_FORMAT).date()
        end_date = datetime.strptime(end_date_str, DATE_FORMAT).date()
        
        date_list = []
        current_date = start_date
        
        while current_date <= end_date:
            date_list.append(current_date.strftime(DATE_FORMAT))
            current_date += timedelta(days=1)
        
        return date_list
    except:
        return []


def calculate_days_between(start_date_str, end_date_str):
    """
    Calculate number of days between two dates (inclusive)
    Args:
        start_date_str: start date "YYYY-MM-DD"
        end_date_str: end date "YYYY-MM-DD"
    Returns: int (number of days)
    """
    if not start_date_str or not end_date_str:
        return 0
    
    try:
        start_date = datetime.strptime(start_date_str, DATE_FORMAT).date()
        end_date = datetime.strptime(end_date_str, DATE_FORMAT).date()
        
        days = (end_date - start_date).days + 1  # +1 to include both start and end
        return max(0, days)
    except:
        return 0


def add_days_to_date(date_str, days):
    """
    Add days to a date
    Args:
        date_str: date string "YYYY-MM-DD"
        days: number of days to add (can be negative)
    Returns: new date string "YYYY-MM-DD"
    """
    if not date_str:
        return None
    
    try:
        original_date = datetime.strptime(date_str, DATE_FORMAT).date()
        new_date = original_date + timedelta(days=days)
        return new_date.strftime(DATE_FORMAT)
    except:
        return None


def is_date_in_range(date_str, start_date_str, end_date_str):
    """
    Check if a date falls within a range (inclusive)
    Args:
        date_str: date to check "YYYY-MM-DD"
        start_date_str: range start "YYYY-MM-DD"
        end_date_str: range end "YYYY-MM-DD"
    Returns: boolean
    """
    if not date_str or not start_date_str or not end_date_str:
        return False
    
    try:
        check_date = datetime.strptime(date_str, DATE_FORMAT).date()
        start_date = datetime.strptime(start_date_str, DATE_FORMAT).date()
        end_date = datetime.strptime(end_date_str, DATE_FORMAT).date()
        
        return start_date <= check_date <= end_date
    except:
        return False


# ============================================================================
# WORK HOURS CALCULATION
# ============================================================================

def calculate_work_hours(check_in_time, check_out_time, date_str=None):
    """
    Calculate work hours between check-in and check-out times
    Args:
        check_in_time: time string "HH:MM:SS"
        check_out_time: time string "HH:MM:SS"
        date_str: optional date string (for handling overnight shifts)
    Returns: float (hours with 2 decimal places)
    """
    if not check_in_time or not check_out_time:
        return 0.0
    
    try:
        # Use today's date or provided date
        if date_str:
            base_date = datetime.strptime(date_str, DATE_FORMAT).date()
        else:
            base_date = datetime.now(KOLKATA_TZ).date()
        
        # Parse times
        check_in = datetime.strptime(check_in_time, TIME_FORMAT).time()
        check_out = datetime.strptime(check_out_time, TIME_FORMAT).time()
        
        # Combine with date
        dt_in = datetime.combine(base_date, check_in)
        dt_out = datetime.combine(base_date, check_out)
        
        # Handle overnight shift (check-out is on next day)
        if check_out < check_in:
            dt_out = dt_out + timedelta(days=1)
        
        # Calculate difference
        time_diff = dt_out - dt_in
        hours = time_diff.total_seconds() / 3600
        
        return round(max(0, hours), 2)
    except:
        return 0.0


def calculate_work_duration_display(check_in_time, check_out_time):
    """
    Calculate work duration in human-readable format
    Args:
        check_in_time: time string "HH:MM:SS"
        check_out_time: time string "HH:MM:SS"
    Returns: string (e.g., "8 hours 30 minutes")
    """
    hours = calculate_work_hours(check_in_time, check_out_time)
    
    if hours == 0:
        return "0 hours"
    
    full_hours = int(hours)
    minutes = int((hours - full_hours) * 60)
    
    if full_hours > 0 and minutes > 0:
        return f"{full_hours} hours {minutes} minutes"
    elif full_hours > 0:
        return f"{full_hours} hours"
    else:
        return f"{minutes} minutes"


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def is_valid_date_format(date_str):
    """
    Validate date string format
    Args:
        date_str: date string to validate
    Returns: boolean
    """
    if not date_str:
        return False
    try:
        datetime.strptime(date_str, DATE_FORMAT)
        return True
    except:
        return False


def is_valid_time_format(time_str):
    """
    Validate time string format
    Args:
        time_str: time string to validate
    Returns: boolean
    """
    if not time_str:
        return False
    try:
        datetime.strptime(time_str, TIME_FORMAT)
        return True
    except:
        return False


def is_valid_datetime_format(datetime_str):
    """
    Validate datetime string format
    Args:
        datetime_str: datetime string to validate
    Returns: boolean
    """
    if not datetime_str:
        return False
    try:
        datetime.strptime(datetime_str, DATETIME_FORMAT)
        return True
    except:
        return False


# ============================================================================
# CONVENIENCE ALIASES
# ============================================================================

now = get_current_datetime_ist
today = get_current_date_ist
current_time = get_current_time_ist