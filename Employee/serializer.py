from rest_framework_mongoengine.serializers import DocumentSerializer, EmbeddedDocumentSerializer
from rest_framework import serializers
from Employee.models import Employee, Address, Documents, Attendance
from Shifts.models import Shift
from Orgnization.models import Organization
from Departments.models import Departments
from utils.timezone_utils import format_date_display, format_time_display, format_datetime_display


# ============== EMBEDDED DOCUMENT SERIALIZERS ==============

class AddressSerializer(EmbeddedDocumentSerializer):
    class Meta:
        model = Address
        fields = "__all__"


class DocumentsSerializer(EmbeddedDocumentSerializer):
    class Meta:
        model = Documents
        fields = "__all__"


# ============== REFERENCE FIELD SERIALIZERS ==============

class ShiftSerializer(DocumentSerializer):
    """Shift serializer with time display formatting"""
    
    from_time_display = serializers.SerializerMethodField()
    end_time_display = serializers.SerializerMethodField()
    late_mark_time_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Shift
        fields = "__all__"
    
    def get_from_time_display(self, obj):
        """Convert 24hr to 12hr format with AM/PM"""
        if obj.fromTime:
            return format_time_display(obj.fromTime)
        return None
    
    def get_end_time_display(self, obj):
        """Convert 24hr to 12hr format with AM/PM"""
        if obj.endTime:
            return format_time_display(obj.endTime)
        return None
    
    def get_late_mark_time_display(self, obj):
        """Convert 24hr to 12hr format with AM/PM"""
        if obj.lateMarkTime:
            return format_time_display(obj.lateMarkTime)
        return None


class OrganizationSerializer(DocumentSerializer):
    """Organization serializer"""
    
    class Meta:
        model = Organization
        fields = "__all__"


class DepartmentSerializer(DocumentSerializer):
    """Department serializer"""
    
    class Meta:
        model = Departments
        fields = "__all__"


# ============== EMPLOYEE SERIALIZER ==============
class EmployeeSerializer(DocumentSerializer):
    """
    Complete Employee serializer with proper reference field expansion
    """
    
    # Embedded documents (read-only nested objects)
    currentAddress_obj = AddressSerializer(source='currentAddress', read_only=True)
    permanentAddress_obj = AddressSerializer(source='permanentAddress', read_only=True)
    documents_obj = DocumentsSerializer(source='documents', read_only=True)
    
    # Reference fields expanded with full details
    organizationId_details = serializers.SerializerMethodField()
    departmentId_details = serializers.SerializerMethodField()
    shiftId_details = serializers.SerializerMethodField()
    
    # CHANGED: Single manager to multiple managers
    reportingManagers_details = serializers.SerializerMethodField()
    
    # Date display fields
    dob_display = serializers.SerializerMethodField()
    doj_display = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
        }
    
    def get_organizationId_details(self, obj):
        """Get full organization details"""
        if obj.organizationId:
            try:
                return {
                    "id": str(obj.organizationId.id),
                    "orgName": obj.organizationId.orgName,
                    "orgLocation": obj.organizationId.orgLocation,
                    "orgContact": obj.organizationId.orgContact,
                    "orgEmail": obj.organizationId.orgEmail,
                    "orgStatus": obj.organizationId.orgStatus
                }
            except:
                return None
        return None
    
    def get_departmentId_details(self, obj):
        """Get full department details"""
        if obj.departmentId:
            try:
                return {
                    "id": str(obj.departmentId.id),
                    "deptName": obj.departmentId.deptName,
                    "deptDescription": getattr(obj.departmentId, 'deptDescription', None)
                }
            except:
                return None
        return None
    
    def get_shiftId_details(self, obj):
        """Get full shift details"""
        if obj.shiftId:
            try:
                return {
                    "id": str(obj.shiftId.id),
                    "shiftType": obj.shiftId.shiftType,
                    "fromTime": obj.shiftId.fromTime,
                    "endTime": obj.shiftId.endTime,
                    "lateMarkTime": obj.shiftId.lateMarkTime,
                    "fromTime_display": format_time_display(obj.shiftId.fromTime) if obj.shiftId.fromTime else None,
                    "endTime_display": format_time_display(obj.shiftId.endTime) if obj.shiftId.endTime else None,
                    "lateMarkTime_display": format_time_display(obj.shiftId.lateMarkTime) if obj.shiftId.lateMarkTime else None
                }
            except:
                return None
        return None
    
    def get_reportingManagers_details(self, obj):
        """Get reporting managers details - now returns a list"""
        if obj.reportingManagers:
            try:
                managers_list = []
                for manager in obj.reportingManagers:
                    if manager:  # Check if manager reference exists
                        managers_list.append({
                            "id": str(manager.id),
                            "firstName": manager.firstName,
                            "lastName": manager.lastName,
                            "email": manager.email,
                            "role": manager.role,
                            "designation": manager.designationId
                        })
                return managers_list
            except:
                return []
        return []
    
    def get_dob_display(self, obj):
        """Format DOB for display"""
        if obj.dob:
            return format_date_display(str(obj.dob))
        return None
    
    def get_doj_display(self, obj):
        """Format DOJ for display"""
        if obj.doj:
            return format_date_display(str(obj.doj))
        return None
    
    def to_representation(self, instance):
        """Customize the output - convert reference fields to IDs"""
        data = super().to_representation(instance)
        
        # Convert reference fields to string IDs for backward compatibility
        if instance.organizationId:
            data['organizationId'] = str(instance.organizationId.id)
        if instance.departmentId:
            data['departmentId'] = str(instance.departmentId.id)
        if instance.shiftId:
            data['shiftId'] = str(instance.shiftId.id)
        
        # CHANGED: Convert list of reporting managers to list of IDs
        if instance.reportingManagers:
            data['reportingManagers'] = [str(manager.id) for manager in instance.reportingManagers if manager]
        else:
            data['reportingManagers'] = []
        
        return data
    
    def create(self, validated_data):
        """Generate password if not provided"""
        if 'password' not in validated_data or not validated_data['password']:
            import random
            import string
            validated_data['password'] = ''.join(
                random.choices(string.ascii_letters + string.digits, k=8)
            )
        return super().create(validated_data)

# ============== ATTENDANCE SERIALIZER ==============

class AttendanceSerializer(DocumentSerializer):
    # Add display fields that show formatted versions
    date_display = serializers.SerializerMethodField()
    check_in_display = serializers.SerializerMethodField()
    check_out_display = serializers.SerializerMethodField()
    created_at_display = serializers.SerializerMethodField()
    updated_at_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Attendance
        fields = "__all__"
        depth = 1

    def get_date_display(self, obj):
        """Return date in DD-MM-YYYY format"""
        if obj.date:
            return format_date_display(obj.date)
        return None
    
    def get_check_in_display(self, obj):
        """Return check_in time in 12-hour format with AM/PM"""
        if obj.check_in_time:
            return format_time_display(obj.check_in_time)
        return None
    
    def get_check_out_display(self, obj):
        """Return check_out time in 12-hour format with AM/PM"""
        if obj.check_out_time:
            return format_time_display(obj.check_out_time)
        return None
    
    def get_created_at_display(self, obj):
        """Return created_at in display format"""
        if obj.created_at:
            return format_datetime_display(obj.created_at)
        return None
    
    def get_updated_at_display(self, obj):
        """Return updated_at in display format"""
        if obj.updated_at:
            return format_datetime_display(obj.updated_at)
        return None

# ============== SIMPLIFIED LIST SERIALIZERS ==============

class EmployeeListSerializer(DocumentSerializer):
    """Simplified employee serializer for list views"""
    
    organization_name = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    shift_type = serializers.SerializerMethodField()
    reporting_manager_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Employee
        fields = [
            'id', 'firstName', 'lastName', 'email', 'mobileNumber',
            'role', 'designationId', 'status', 'doj', 'organization_name',
            'department_name', 'shift_type', 'reporting_manager_name'
        ]
    
    def get_organization_name(self, obj):
        return obj.organizationId.orgName if obj.organizationId else None
    
    def get_department_name(self, obj):
        return obj.departmentId.deptName if obj.departmentId else None
    
    def get_shift_type(self, obj):
        return obj.shiftId.shiftType if obj.shiftId else None
    
    def get_reporting_manager_name(self, obj):
        if obj.reportingManager:
            return f"{obj.reportingManager.firstName} {obj.reportingManager.lastName}"
        return None


class AttendanceListSerializer(DocumentSerializer):
    """Simplified attendance serializer for list views"""
    
    employee_name = serializers.SerializerMethodField()
    employee_email = serializers.SerializerMethodField()
    date_display = serializers.SerializerMethodField()
    check_in_display = serializers.SerializerMethodField()
    check_out_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Attendance
        fields = [
            'id', 'date', 'status', 'check_in_time', 'check_out_time',
            'total_work_hours', 'is_late', 'employee_name', 'employee_email',
            'date_display', 'check_in_display', 'check_out_display'
        ]
    
    def get_employee_name(self, obj):
        if obj.employee:
            return f"{obj.employee.firstName} {obj.employee.lastName}"
        return None
    
    def get_employee_email(self, obj):
        return obj.employee.email if obj.employee else None
    
    def get_date_display(self, obj):
        return format_date_display(obj.date) if obj.date else None
    
    def get_check_in_display(self, obj):
        return format_time_display(obj.check_in_time) if obj.check_in_time else None
    
    def get_check_out_display(self, obj):
        return format_time_display(obj.check_out_time) if obj.check_out_time else None