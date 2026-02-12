# from utils.timezone_utils import is_valid_date_format
# def apply_date_filters(queryset, request):
#     date = request.query_params.get("date")
#     month = request.query_params.get("month")
#     year = request.query_params.get("year")

#     # Exact day
#     if date and is_valid_date_format(date):
#         return queryset.filter(date=date)

#     # Month view (HR / calendar)
#     if month and year:
#         month = month.zfill(2)
#         start = f"{year}-{month}-01"
#         end = f"{year}-{month}-31"
#         return queryset.filter(date__gte=start, date__lte=end)

#     # Default → return all records for employee
#     return queryset


# def apply_wfh_date_filters(queryset, request):
#     """For WFH requests with start_date and end_date fields"""
#     date = request.query_params.get("date")
#     month = request.query_params.get("month")
#     year = request.query_params.get("year")
    
#     # Exact day - check if WFH request overlaps with this date
#     if date and is_valid_date_format(date):
#         return queryset.filter(start_date__lte=date, end_date__gte=date)
    
#     # Month view - check if WFH request overlaps with this month
#     if month and year:
#         month = month.zfill(2)
#         start = f"{year}-{month}-01"
#         end = f"{year}-{month}-31"
#         # Get requests that overlap with the month range
#         return queryset.filter(start_date__lte=end, end_date__gte=start)
    
#     # Default → return all records
#     return queryset


# def apply_leave_date_filters(queryset, request):
#     """For Leave requests with start_date and end_date fields"""
#     date = request.query_params.get("date")
#     month = request.query_params.get("month")
#     year = request.query_params.get("year")
    
#     # Exact day - check if leave request overlaps with this date
#     if date and is_valid_date_format(date):
#         return queryset.filter(start_date__lte=date, end_date__gte=date)
    
#     # Month view - check if leave request overlaps with this month
#     if month and year:
#         month = month.zfill(2)
#         start = f"{year}-{month}-01"
#         end = f"{year}-{month}-31"
#         # Get requests that overlap with the month range
#         return queryset.filter(start_date__lte=end, end_date__gte=start)
    
#     # Default → return all records
#     return queryset






from utils.timezone_utils import is_valid_date_format


# ============================================================================
# COMMON DATE FILTER (Single date field)
# Example: Attendance, Holiday, Daily Logs
# ============================================================================

def apply_date_filters(queryset, request):
    """
    Filters records having a single `date` field.

    Supported query params:
    ?date=YYYY-MM-DD
    ?month=MM&year=YYYY
    ?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
    """

    date = request.query_params.get("date")
    month = request.query_params.get("month")
    year = request.query_params.get("year")
    start_date = request.query_params.get("start_date")
    end_date = request.query_params.get("end_date")

    # --------------------------------------------------
    # 1️⃣ DATE RANGE FILTER
    # --------------------------------------------------
    if (
        start_date
        and end_date
        and is_valid_date_format(start_date)
        and is_valid_date_format(end_date)
    ):
        return queryset.filter(
            date__gte=start_date,
            date__lte=end_date
        )

    # --------------------------------------------------
    # 2️⃣ EXACT DATE
    # --------------------------------------------------
    if date and is_valid_date_format(date):
        return queryset.filter(date=date)

    # --------------------------------------------------
    # 3️⃣ MONTH FILTER
    # --------------------------------------------------
    if month and year:
        month = month.zfill(2)
        start = f"{year}-{month}-01"
        end = f"{year}-{month}-31"

        return queryset.filter(
            date__gte=start,
            date__lte=end
        )

    return queryset


# ============================================================================
# WFH DATE FILTER (start_date & end_date fields)
# ============================================================================

def apply_wfh_date_filters(queryset, request):
    """
    For WFH requests having:
    start_date and end_date

    Returns records overlapping with filter range.
    """

    date = request.query_params.get("date")
    month = request.query_params.get("month")
    year = request.query_params.get("year")
    filter_start = request.query_params.get("start_date")
    filter_end = request.query_params.get("end_date")

    # --------------------------------------------------
    # 1️⃣ DATE RANGE OVERLAP FILTER
    # --------------------------------------------------
    if (
        filter_start
        and filter_end
        and is_valid_date_format(filter_start)
        and is_valid_date_format(filter_end)
    ):
        return queryset.filter(
            start_date__lte=filter_end,
            end_date__gte=filter_start
        )

    # --------------------------------------------------
    # 2️⃣ EXACT DATE
    # --------------------------------------------------
    if date and is_valid_date_format(date):
        return queryset.filter(
            start_date__lte=date,
            end_date__gte=date
        )

    # --------------------------------------------------
    # 3️⃣ MONTH FILTER
    # --------------------------------------------------
    if month and year:
        month = month.zfill(2)
        start = f"{year}-{month}-01"
        end = f"{year}-{month}-31"

        return queryset.filter(
            start_date__lte=end,
            end_date__gte=start
        )

    return queryset


# ============================================================================
# LEAVE DATE FILTER (start_date & end_date fields)
# ============================================================================

def apply_leave_date_filters(queryset, request):
    """
    For Leave requests having:
    start_date and end_date

    Returns records overlapping with filter range.
    """

    date = request.query_params.get("date")
    month = request.query_params.get("month")
    year = request.query_params.get("year")
    filter_start = request.query_params.get("start_date")
    filter_end = request.query_params.get("end_date")

    # --------------------------------------------------
    # 1️⃣ DATE RANGE OVERLAP FILTER
    # --------------------------------------------------
    if (
        filter_start
        and filter_end
        and is_valid_date_format(filter_start)
        and is_valid_date_format(filter_end)
    ):
        return queryset.filter(
            start_date__lte=filter_end,
            end_date__gte=filter_start
        )

    # --------------------------------------------------
    # 2️⃣ EXACT DATE
    # --------------------------------------------------
    if date and is_valid_date_format(date):
        return queryset.filter(
            start_date__lte=date,
            end_date__gte=date
        )

    # --------------------------------------------------
    # 3️⃣ MONTH FILTER
    # --------------------------------------------------
    if month and year:
        month = month.zfill(2)
        start = f"{year}-{month}-01"
        end = f"{year}-{month}-31"

        return queryset.filter(
            start_date__lte=end,
            end_date__gte=start
        )

    return queryset
