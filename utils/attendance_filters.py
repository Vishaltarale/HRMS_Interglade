"""
Attendance filtering utilities for string-based date queries
"""
from datetime import datetime


def apply_month_year_filter(queryset, request):
    """
    Filter attendance by month and year using string dates
    
    Args:
        queryset: MongoEngine queryset
        request: Django request object with query params
    
    Expected query params:
        - month: int (1-12)
        - year: int (e.g., 2024)
    
    Returns:
        Filtered queryset
    """
    month = request.query_params.get('month')
    year = request.query_params.get('year')
    
    if month and year:
        try:
            month = int(month)
            year = int(year)
            
            # Create date range strings for the month
            # Start: YYYY-MM-01
            # End: YYYY-MM-31 (or appropriate last day)
            
            # Get last day of month
            if month == 12:
                next_month = 1
                next_year = year + 1
            else:
                next_month = month + 1
                next_year = year
            
            # First day of current month
            start_date = f"{year:04d}-{month:02d}-01"
            
            # First day of next month (to use as upper bound)
            end_date = f"{next_year:04d}-{next_month:02d}-01"
            
            # Filter: date >= start_date AND date < end_date
            queryset = queryset.filter(date__gte=start_date, date__lt=end_date)
            
        except (ValueError, TypeError):
            pass  # Invalid month/year, return unfiltered
    
    return queryset


def apply_status_filter(queryset, request):
    """
    Filter attendance by status
    
    Args:
        queryset: MongoEngine queryset
        request: Django request object with query params
    
    Expected query params:
        - status: str (present, latemark, absent, half_day, WFH, on_leave)
    
    Returns:
        Filtered queryset
    """
    status = request.query_params.get('status')
    
    if status:
        valid_statuses = ["present", "latemark", "pending", "absent", "WFH", "half_day", "on_leave"]
        if status in valid_statuses:
            queryset = queryset.filter(status=status)
    
    return queryset


def apply_date_range_filter(queryset, request):
    """
    Filter attendance by date range using string dates
    
    Args:
        queryset: MongoEngine queryset
        request: Django request object with query params
    
    Expected query params:
        - start_date: str (YYYY-MM-DD)
        - end_date: str (YYYY-MM-DD)
    
    Returns:
        Filtered queryset
    """
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    if start_date:
        try:
            # Validate format
            datetime.strptime(start_date, "%Y-%m-%d")
            queryset = queryset.filter(date__gte=start_date)
        except ValueError:
            pass  # Invalid format, skip filter
    
    if end_date:
        try:
            # Validate format
            datetime.strptime(end_date, "%Y-%m-%d")
            queryset = queryset.filter(date__lte=end_date)
        except ValueError:
            pass  # Invalid format, skip filter
    
    return queryset


def apply_employee_filter(queryset, request):
    """
    Filter attendance by employee ID
    
    Args:
        queryset: MongoEngine queryset
        request: Django request object with query params
    
    Expected query params:
        - employee_id: str (ObjectId as string)
    
    Returns:
        Filtered queryset
    """
    employee_id = request.query_params.get('employee_id')
    
    if employee_id:
        from bson import ObjectId
        try:
            queryset = queryset.filter(employee=ObjectId(employee_id))
        except:
            pass  # Invalid ObjectId, return unfiltered
    
    return queryset