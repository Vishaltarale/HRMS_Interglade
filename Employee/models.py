from mongoengine import Document, StringField, IntField, EmailField, EmbeddedDocument, \
                        EmbeddedDocumentField, DateField, ReferenceField, BooleanField, FloatField, ListField
from Orgnization.models import Organization
from Departments.models import Departments
from Shifts.models import Shift


class LeavePolicy(EmbeddedDocument):
    """Embedded version of Leave Policy"""
    policy_name = StringField(default="Annual Leave Policy")
    
    # Leave Entitlements
    earned_leave_days = IntField(default=18)
    earned_leave_monthly = FloatField(default=1.5)
    special_leave_days = IntField(default=1)
    
    # Notice Periods
    planned_notice_days = IntField(default=10)
    regular_notice_days = IntField(default=2)
    
    # Approval
    approver_roles = ListField(StringField(), default=['hr', 'admin', 'SR_employee'])
    
    # Probation
    probation_days = IntField(default=90)
    
    # Year
    leave_year_start = IntField(default=1)
    leave_year_end = IntField(default=12)
    
    is_active = BooleanField(default=True)


class Address(EmbeddedDocument):
    street = StringField(required=True, max_length=255)
    city = StringField(required=True, max_length=100)
    state = StringField(required=True, max_length=100)
    zip = StringField(required=True, max_length=20)
    country = StringField(required=True, max_length=100)


class Documents(EmbeddedDocument):
    adharCard = StringField(required=False)
    panCard = StringField(required=False)
    bankBook = StringField(required=False)
    xStandardMarksheet = StringField(required=False)
    xiiStandardMarksheet = StringField(required=False)
    degree = StringField(required=False)
    experienceLetter = StringField(required=False)
    photo = StringField(required=False)


class Employee(Document):
    firstName = StringField(required=True, max_length=100)
    middleName = StringField(max_length=100)
    lastName = StringField(required=True, max_length=100)

    location = StringField()
    email = EmailField(required=True, unique=True)
    password = StringField(required=False) 
    mobileNumber = StringField(required=True, regex=r'^\d{10}$')

    gender = StringField(required=True, choices=('male', 'female', 'other'))

    dob = DateField(required=True)  
    doj = DateField(required=True)  

    status = StringField(required=True, choices=('active', 'inactive'))
    role = StringField(required=True, choices=('admin', 'hr', 'JR_employee', 'SR_employee'))

    # reportingManager = ReferenceField("Employee", required=False)
    reportingManagers = ListField(ReferenceField("Employee"), required=False, default=list)
    # Relations
    organizationId = ReferenceField(Organization, required=True, reverse_delete_rule=0)
    departmentId = ReferenceField(Departments, required=True, reverse_delete_rule=0)
    designationId = StringField(max_length=100)
    shiftId = ReferenceField(Shift, required=True, reverse_delete_rule=0)

    # Embedded Documents
    currentAddress = EmbeddedDocumentField(Address, required=True)
    permanentAddress = EmbeddedDocumentField(Address, required=True)
    documents = EmbeddedDocumentField(Documents)
    policy = EmbeddedDocumentField(LeavePolicy)

    def __init__(self, *args, **kwargs):
        # CRITICAL: Remove old reportingManager field before initialization
        # This prevents MongoEngine from throwing FieldDoesNotExist error
        if 'reportingManager' in kwargs:
            old_manager = kwargs.pop('reportingManager')
            # If reportingManagers not set, convert old single manager to list
            if 'reportingManagers' not in kwargs or not kwargs['reportingManagers']:
                if old_manager:
                    kwargs['reportingManagers'] = [old_manager]
        
        super().__init__(*args, **kwargs)
        
        # If policy is None, set it to default LeavePolicy
        if self.policy is None:
            self.policy = LeavePolicy()

    @property
    def is_authenticated(self):
        return True

    meta = {
        "collection": "employees",
        "strict": True
    }


class Attendance(Document):
    """
    Attendance model with string-based datetime storage in IST
    
    Date format: "YYYY-MM-DD" (e.g., "2024-12-27")
    Time format: "HH:MM:SS" in 24-hour IST (e.g., "09:30:00", "18:45:30")
    """
    employee = ReferenceField(Employee, required=True, reverse_delete_rule=2)

    # Date stored as string in "YYYY-MM-DD" format
    date = StringField(required=True)
    
    # Time stored as string in "HH:MM:SS" format (IST timezone)
    check_in_time = StringField()  # e.g., "09:30:00"
    check_out_time = StringField()  # e.g., "18:30:00"

    is_valid = BooleanField(default=False)
    is_late = BooleanField(default=False)
    is_onWFH = BooleanField(default=False)

    total_work_hours = FloatField()
    break_hours = FloatField()

    status = StringField(
        choices=["present", "latemark", "pending", "absent", "wfh", "half_day", "on_leave"],
        default="pending"
    )
    
    check_in_location = StringField()
    check_out_location = StringField()

    # Auto detected device 
    check_in_ip = StringField()
    check_in_device = StringField()    

    check_out_ip = StringField()  
    check_out_device = StringField()      

    is_overtime = BooleanField(default=False)
    overtime_hours = FloatField()

    remarks = StringField()
    
    # Audit fields stored as string in IST (full datetime for audit)
    created_at = StringField()  # "YYYY-MM-DD HH:MM:SS"
    updated_at = StringField()  # "YYYY-MM-DD HH:MM:SS"

    meta = {
        "collection": "attendance",
        "strict": True,
        "indexes": [
            ("employee", "date"),  # Compound index for faster queries
            "date",
            "status"
        ]
    }


class TokenBlacklist(Document):
    token = StringField(required=True, unique=True)
    empId = StringField(required=True, max_length=255)
    blacklisted_at = StringField(required=True)  # "YYYY-MM-DD HH:MM:SS" IST
    expires_at = StringField(required=True)  # "YYYY-MM-DD HH:MM:SS" IST
    
    meta = {
        "collection": "token_blacklist",
        "indexes": [
            'token',
            'empId'
        ],
        "strict": True
    }
    
    def __str__(self):
        return f"Blacklisted token for {self.empId}"