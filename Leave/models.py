from mongoengine import (
    Document, EmbeddedDocument, EmbeddedDocumentField, ReferenceField, 
    StringField, DateField, DateTimeField, BooleanField, IntField, 
    FloatField, ListField, DictField
)
from datetime import datetime
from utils.timezone_utils import get_current_date_ist, get_current_datetime_ist

# Leave Request Model
# Updated LeaveRequest Model - Replace in your models.py

class LeaveRequest(Document):
    """
    Employee Leave Request with IST string-based dates
    
    Date format: "YYYY-MM-DD" (e.g., "2024-12-27")
    DateTime format: "YYYY-MM-DD HH:MM:SS" (e.g., "2024-12-27 14:30:00")
    """
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('CANCELLED', 'Cancelled'),
        ('REJECTED', 'Rejected'),
    ]
    
    LEAVE_TYPE_CHOICES = [
        ('PL', 'Paid Leave'),
        ('SPL', 'Special Leave'),
        ('UPL', 'Unpaid Leave'),
        ('SL', 'Sick Leave')
    ]
    
    # Employee Details
    employee = ReferenceField('Employee')
    employee_name = StringField()  # Cache for easy display
    employee_department = StringField()
    
    # CHANGED: Support multiple reporting managers
    reporting_managers = ListField(ReferenceField('Employee'))  # List of all reporting managers
    
    # Leave Details
    leave_type = StringField(choices=LEAVE_TYPE_CHOICES, required=True)
    
    # Dates stored as strings in "YYYY-MM-DD" format (IST timezone)
    start_date = StringField(required=True)  # e.g., "2024-12-27"
    end_date = StringField(required=True)    # e.g., "2024-12-30"
    total_days = FloatField(default=0.0)
    
    # Request Info
    reason = StringField(required=True)
    applied_date = StringField()  # "YYYY-MM-DD HH:MM:SS" in IST
    is_planned = BooleanField(default=False)  # True = planned leave (10 days notice)
    is_emergency = BooleanField(default=False)  # True = emergency (no notice)
    
    # Status
    status = StringField(choices=STATUS_CHOICES, default='PENDING')
    
    # Approval - DateTime stored as strings in IST
    # CHANGED: Track which reporting manager can approve (any one from the list)
    current_approvers = ListField(ReferenceField('Employee'))  # All possible approvers
    approved_by = ReferenceField('Employee')  # The one who actually approved
    approved_date = StringField()  # "YYYY-MM-DD HH:MM:SS" in IST

    rejection_reason = StringField()
    rejected_by = ReferenceField("Employee")
    rejected_date = StringField()  # "YYYY-MM-DD HH:MM:SS" in IST

    # Probation Check
    is_on_probation = BooleanField(default=False)
    
    # Balance Check
    has_sufficient_balance = BooleanField(default=True)
    
    # Metadata - DateTime stored as strings in IST
    created_at = StringField()  # "YYYY-MM-DD HH:MM:SS" in IST
    updated_at = StringField()  # "YYYY-MM-DD HH:MM:SS" in IST
    
    meta = {
        'collection': 'leave_requests',
        'indexes': [
            'employee',
            'status',
            'start_date',
            'leave_type',
            {'fields': ['employee', 'status']},
            {'fields': ['start_date', 'end_date']},
        ],
        'ordering': ['-applied_date']
    }
    
    def clean(self):
        """Set calculated fields"""
        from utils.timezone_utils import compare_dates, get_current_date_ist, get_current_datetime_ist
        
        # Set timestamps if not set
        current_datetime = get_current_datetime_ist()
        if not self.applied_date:
            self.applied_date = current_datetime
        if not self.created_at:
            self.created_at = current_datetime
        self.updated_at = current_datetime
        
        # Set employee name
        if self.employee and not self.employee_name:
            self.employee_name = f"{self.employee.firstName} {self.employee.lastName}"
            self.employee_department = self.employee.departmentId.deptName if self.employee.departmentId else ""
        
        # CHANGED: Set reporting managers list
        if not self.reporting_managers and self.employee:
            if hasattr(self.employee, 'reportingManagers') and self.employee.reportingManagers:
                self.reporting_managers = list(self.employee.reportingManagers)
            else:
                self.reporting_managers = []
        
        # CHANGED: Set current approvers as all reporting managers
        if not self.current_approvers and self.reporting_managers:
            self.current_approvers = list(self.reporting_managers)

        # Calculate total days using string comparison
        if self.start_date and self.end_date:
            # Convert string dates to date objects for calculation
            try:
                from datetime import datetime
                start = datetime.strptime(self.start_date, "%Y-%m-%d").date()
                end = datetime.strptime(self.end_date, "%Y-%m-%d").date()
                days = (end - start).days + 1
                self.total_days = float(days)
            except:
                self.total_days = 1.0
        
        # Check if employee is on probation
        if self.employee and self.employee.doj:
            from datetime import date, timedelta
            # Calculate probation end (90 days from DOJ)
            probation_days = self.employee.policy.probation_days if self.employee.policy else 90
            probation_end = self.employee.doj + timedelta(days=probation_days)
            self.is_on_probation = date.today() < probation_end


# Updated WFH Model - Replace in your models.py
class WFH(Document):
    """
    Work From Home Request Model
    """
    employee = ReferenceField('Employee', required=True)
    start_date = StringField(required=True)  # e.g., "2024-12-27"
    end_date = StringField(required=True)  # e.g., "2024-12-28"
    total_days = FloatField(default=0.0)
    reason = StringField(required=True)
    
    # CHANGED: Support multiple reporting managers
    reporting_managers = ListField(ReferenceField('Employee'))  # List of all reporting managers
    
    status = StringField(
        choices=['pending', 'approved', 'rejected'],
        default='pending'
    )

    # CHANGED: Track which reporting managers can approve
    current_approvers = ListField(ReferenceField('Employee'))  # All possible approvers
    applied_date = StringField()  # "YYYY-MM-DD HH:MM:SS" in IST
    approved_by = ReferenceField('Employee')  # The one who actually approved
    approved_date = StringField()  # "YYYY-MM-DD HH:MM:SS" in IST
    rejected_by = ReferenceField('Employee')
    rejected_date = StringField()  # "YYYY-MM-DD HH:MM:SS" in IST
    rejection_reason = StringField()
    
    created_at = StringField()  # "YYYY-MM-DD HH:MM:SS" in IST
    updated_at = StringField()  # "YYYY-MM-DD HH:MM:SS" in IST
    
    meta = {
        'collection': 'wfh_requests',
        'indexes': [
            'employee',
            'status',
            {'fields': ['employee', 'start_date', 'end_date'], 'unique': True}
        ],
        'ordering': ['-applied_date']
    }

    def clean(self):
        """Set calculated fields"""
        from utils.timezone_utils import compare_dates, get_current_date_ist, get_current_datetime_ist
        
        # Set timestamps if not set
        current_datetime = get_current_datetime_ist()
        if not self.applied_date:
            self.applied_date = current_datetime
        if not self.created_at:
            self.created_at = current_datetime
        self.updated_at = current_datetime
        
        # CHANGED: Set reporting managers list
        if not self.reporting_managers and self.employee:
            if hasattr(self.employee, 'reportingManagers') and self.employee.reportingManagers:
                self.reporting_managers = list(self.employee.reportingManagers)
            else:
                self.reporting_managers = []
        
        # CHANGED: Set current approvers as all reporting managers
        if not self.current_approvers and self.reporting_managers:
            self.current_approvers = list(self.reporting_managers)

        # Calculate total days using string comparison
        if self.start_date and self.end_date:
            # Convert string dates to date objects for calculation
            try:
                from datetime import datetime
                start = datetime.strptime(self.start_date, "%Y-%m-%d").date()
                end = datetime.strptime(self.end_date, "%Y-%m-%d").date()
                days = (end - start).days + 1
                self.total_days = float(days)
            except:
                self.total_days = 1.0
        
        # Check if employee is on probation
        if self.employee and self.employee.doj:
            from datetime import date, timedelta
            # Calculate probation end (90 days from DOJ)
            probation_days = self.employee.policy.probation_days if self.employee.policy else 90
            probation_end = self.employee.doj + timedelta(days=probation_days)
            self.is_on_probation = date.today() < probation_end

                
#-------------------------------------------------------------------------Holiday Model----------------------------------------------------------------------------------------------

from mongoengine import (
    Document, StringField, DateField, BooleanField, 
    ListField, IntField, DictField
)
from datetime import datetime
from utils.timezone_utils import get_current_datetime_ist

class Holiday(Document):
    """
    Holiday Model for HRMS
    Manages company-wide holidays that affect leave calculations and calendar
    """
    
    HOLIDAY_TYPE_CHOICES = [
        ('NATIONAL', 'National Holiday'),
        ('REGIONAL', 'Regional Holiday'),
        ('COMPANY', 'Company Holiday'),
        ('OPTIONAL', 'Optional Holiday'),
        ('RESTRICTED', 'Restricted Holiday')
    ]
    
    # Basic Details
    name = StringField(required=True, max_length=200)
    date = StringField(required=True)  # "YYYY-MM-DD" format in IST
    holiday_type = StringField(choices=HOLIDAY_TYPE_CHOICES, default='COMPANY')
    
    # Additional Info
    description = StringField(max_length=500)
    is_active = BooleanField(default=True)
    
    # Applicability
    year = IntField(required=True)
    applicable_departments = ListField(StringField())  # Empty = all departments
    applicable_locations = ListField(StringField())  # Empty = all locations
    
    # Optional Holiday Management (for types like 'OPTIONAL' or 'RESTRICTED')
    is_optional = BooleanField(default=False)  # Can employees choose to work?
    max_optional_selections = IntField(default=0)  # Max optional holidays per employee
    
    # Metadata
    created_by = StringField()  # HR user who created
    created_at = StringField()  # "YYYY-MM-DD HH:MM:SS" in IST
    updated_at = StringField()  # "YYYY-MM-DD HH:MM:SS" in IST
    
    meta = {
        'collection': 'holidays',
        'indexes': [
            'date',
            'year',
            'holiday_type',
            'is_active',
            {'fields': ['year', 'date'], 'unique': True}
        ],
        'ordering': ['date']
    }
    
    def clean(self):
        """Set calculated fields"""
        from utils.timezone_utils import get_current_datetime_ist
        
        current_datetime = get_current_datetime_ist()
        
        if not self.created_at:
            self.created_at = current_datetime
        
        self.updated_at = current_datetime
        
        # Extract year from date
        if self.date:
            try:
                from datetime import datetime
                date_obj = datetime.strptime(self.date, "%Y-%m-%d")
                self.year = date_obj.year
            except:
                pass
    
    def is_applicable_to_employee(self, employee):
        """
        Check if holiday applies to a specific employee
        """
        # If no specific departments/locations, applies to all
        if not self.applicable_departments and not self.applicable_locations:
            return True
        
        # Check department
        if self.applicable_departments:
            emp_dept = employee.departmentId.deptName if employee.departmentId else None
            if emp_dept not in self.applicable_departments:
                return False
        
        # Check location
        if self.applicable_locations:
            emp_location = getattr(employee, 'location', None)
            if emp_location not in self.applicable_locations:
                return False
        
        return True