from rest_framework_mongoengine.serializers import DocumentSerializer
from rest_framework_mongoengine import serializers as mongoserializers
from rest_framework import serializers
from Leave.models import LeaveRequest, WFH
from Employee.models import Employee
from utils.timezone_utils import (
    get_current_datetime_ist, 
    get_current_date_ist,
    is_valid_date_format,
    calculate_days_between
)
from datetime import datetime


class LeaveSerializer(DocumentSerializer):
    # Display fields (read-only)
    start_date_display = serializers.SerializerMethodField()
    end_date_display = serializers.SerializerMethodField()
    applied_date_display = serializers.SerializerMethodField()
    approved_date_display = serializers.SerializerMethodField()
    rejected_date_display = serializers.SerializerMethodField()

    class Meta:
        model = LeaveRequest
        fields = "__all__"
        read_only_fields = [
            'employee_name', 
            'employee_department', 
            'total_days',
            'is_on_probation',
            'applied_date',
            'created_at',
            'updated_at'
        ]
    
    def get_start_date_display(self, obj):
        """Format start date for display (DD-MM-YYYY)"""
        if obj.start_date:
            try:
                dt = datetime.strptime(obj.start_date, "%Y-%m-%d")
                return dt.strftime("%d-%m-%Y")
            except:
                return obj.start_date
        return None
    
    def get_end_date_display(self, obj):
        """Format end date for display (DD-MM-YYYY)"""
        if obj.end_date:
            try:
                dt = datetime.strptime(obj.end_date, "%Y-%m-%d")
                return dt.strftime("%d-%m-%Y")
            except:
                return obj.end_date
        return None
    
    def get_applied_date_display(self, obj):
        """Format applied datetime for display"""
        if obj.applied_date:
            try:
                dt = datetime.strptime(obj.applied_date, "%Y-%m-%d %H:%M:%S")
                return dt.strftime("%d-%m-%Y %I:%M:%S %p")
            except:
                return obj.applied_date
        return None
    
    def get_approved_date_display(self, obj):
        """Format approved datetime for display"""
        if obj.approved_date:
            try:
                dt = datetime.strptime(obj.approved_date, "%Y-%m-%d %H:%M:%S")
                return dt.strftime("%d-%m-%Y %I:%M:%S %p")
            except:
                return obj.approved_date
        return None
    
    def get_rejected_date_display(self, obj):
        """Format rejected datetime for display"""
        if obj.rejected_date:
            try:
                dt = datetime.strptime(obj.rejected_date, "%Y-%m-%d %H:%M:%S")
                return dt.strftime("%d-%m-%Y %I:%M:%S %p")
            except:
                return obj.rejected_date
        return None
    
    def validate_start_date(self, value):
        """Validate start date format"""
        if not is_valid_date_format(value):
            raise serializers.ValidationError(
                "Invalid date format. Use YYYY-MM-DD (e.g., 2024-12-27)"
            )
        return value
    
    def validate_end_date(self, value):
        """Validate end date format"""
        if not is_valid_date_format(value):
            raise serializers.ValidationError(
                "Invalid date format. Use YYYY-MM-DD (e.g., 2024-12-27)"
            )
        return value
    
    def validate(self, data):
        """Validate leave request data"""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        # Validate date range
        if start_date and end_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d").date()
                end = datetime.strptime(end_date, "%Y-%m-%d").date()
                
                if end < start:
                    raise serializers.ValidationError({
                        "end_date": "End date cannot be before start date"
                    })
                
                # Check if dates are in the past
                current_date_str = get_current_date_ist()
                current_date = datetime.strptime(current_date_str, "%Y-%m-%d").date()
                
                if start < current_date:
                    raise serializers.ValidationError({
                        "start_date": "Cannot apply for leave in the past"
                    })
            except ValueError as e:
                raise serializers.ValidationError({
                    "dates": "Invalid date format"
                })
        
        return data
    
    def create(self, validated_data):
        """Create a new leave request with IST timestamps"""
        request = self.context.get('request')

        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("User must be authenticated")

        try:
            # Get employee instance for current user
            employee = Employee.objects.get(email=request.user.email)
        except Employee.DoesNotExist:
            raise serializers.ValidationError("Employee profile not found")
        
        # Set employee
        validated_data['employee'] = employee
        
        # Set IST timestamps
        current_datetime = get_current_datetime_ist()
        validated_data['applied_date'] = current_datetime
        validated_data['created_at'] = current_datetime
        validated_data['updated_at'] = current_datetime
        
        # Create leave request
        leave_request = LeaveRequest(**validated_data)
        
        # Run clean to set calculated fields
        leave_request.clean()
        
        # Save the instance
        leave_request.save()
        
        return leave_request
    
    def update(self, instance, validated_data):
        """Update leave request with IST timestamp"""
        # Update timestamp
        validated_data['updated_at'] = get_current_datetime_ist()
        
        # Update fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Run clean to recalculate fields
        instance.clean()
        
        # Save
        instance.save()
        
        return instance


class WFHSerializer(serializers.Serializer):
    """MongoDB-compatible WFH Serializer with IST timezone support"""
    
    # Read-only fields (displayed in response)
    id = serializers.CharField(read_only=True)
    employee = serializers.SerializerMethodField(read_only=True)
    reporting_manager = serializers.SerializerMethodField(read_only=True)
    approved_by = serializers.SerializerMethodField(read_only=True)
    rejected_by = serializers.SerializerMethodField(read_only=True)
    current_approver = serializers.SerializerMethodField(read_only=True)
    
    # Write fields (required for creation)
    start_date = serializers.CharField(required=True)
    end_date = serializers.CharField(required=True)
    reason = serializers.CharField(max_length=500, required=True)
    
    # Optional fields
    remarks = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    # Auto-calculated/read-only fields
    status = serializers.CharField(read_only=True)
    total_days = serializers.IntegerField(read_only=True)
    applied_date = serializers.CharField(read_only=True)
    approved_date = serializers.CharField(read_only=True, required=False, allow_null=True)
    rejected_date = serializers.CharField(read_only=True, required=False, allow_null=True)
    rejection_reason = serializers.CharField(read_only=True, required=False, allow_blank=True)
    created_at = serializers.CharField(read_only=True)
    updated_at = serializers.CharField(read_only=True)
    
    # Display fields (formatted dates)
    start_date_display = serializers.SerializerMethodField(read_only=True)
    end_date_display = serializers.SerializerMethodField(read_only=True)
    applied_date_display = serializers.SerializerMethodField(read_only=True)
    approved_date_display = serializers.SerializerMethodField(read_only=True)
    rejected_date_display = serializers.SerializerMethodField(read_only=True)
    
    def get_employee(self, obj):
        """Get employee details"""
        if hasattr(obj, 'employee') and obj.employee:
            try:
                return {
                    "id": str(obj.employee.id),
                    "firstName": obj.employee.firstName,
                    "lastName": obj.employee.lastName,
                    "email": obj.employee.email,
                    "department": obj.employee.departmentId.deptName if hasattr(obj.employee, 'departmentId') and obj.employee.departmentId else None,
                    "role": obj.employee.role if hasattr(obj.employee, 'role') else None
                }
            except Exception as e:
                return None
        return None
    
    def get_reporting_manager(self, obj):
        """Get reporting manager details"""
        if hasattr(obj, 'reporting_manager') and obj.reporting_manager:
            try:
                return {
                    "id": str(obj.reporting_manager.id),
                    "firstName": obj.reporting_manager.firstName,
                    "lastName": obj.reporting_manager.lastName,
                    "email": obj.reporting_manager.email
                }
            except Exception as e:
                return None
        return None
    
    def get_approved_by(self, obj):
        """Get approver details"""
        if hasattr(obj, 'approved_by') and obj.approved_by:
            try:
                return {
                    "id": str(obj.approved_by.id),
                    "firstName": obj.approved_by.firstName,
                    "lastName": obj.approved_by.lastName,
                    "email": obj.approved_by.email
                }
            except Exception as e:
                return None
        return None
    
    def get_rejected_by(self, obj):
        """Get rejector details"""
        if hasattr(obj, 'rejected_by') and obj.rejected_by:
            try:
                return {
                    "id": str(obj.rejected_by.id),
                    "firstName": obj.rejected_by.firstName,
                    "lastName": obj.rejected_by.lastName,
                    "email": obj.rejected_by.email
                }
            except Exception as e:
                return None
        return None
    
    def get_current_approver(self, obj):
        """Get current approver details"""
        if hasattr(obj, 'current_approver') and obj.current_approver:
            try:
                return {
                    "id": str(obj.current_approver.id),
                    "firstName": obj.current_approver.firstName,
                    "lastName": obj.current_approver.lastName,
                    "email": obj.current_approver.email
                }
            except Exception as e:
                return None
        return None
    
    def get_start_date_display(self, obj):
        """Format start date for display (DD-MM-YYYY)"""
        if hasattr(obj, 'start_date') and obj.start_date:
            try:
                dt = datetime.strptime(obj.start_date, "%Y-%m-%d")
                return dt.strftime("%d-%m-%Y")
            except:
                return str(obj.start_date)
        return None
    
    def get_end_date_display(self, obj):
        """Format end date for display (DD-MM-YYYY)"""
        if hasattr(obj, 'end_date') and obj.end_date:
            try:
                dt = datetime.strptime(obj.end_date, "%Y-%m-%d")
                return dt.strftime("%d-%m-%Y")
            except:
                return str(obj.end_date)
        return None
    
    def get_applied_date_display(self, obj):
        """Format applied datetime for display"""
        if hasattr(obj, 'applied_date') and obj.applied_date:
            try:
                dt = datetime.strptime(obj.applied_date, "%Y-%m-%d %H:%M:%S")
                return dt.strftime("%d-%m-%Y %I:%M:%S %p")
            except:
                return str(obj.applied_date)
        return None
    
    def get_approved_date_display(self, obj):
        """Format approved datetime for display"""
        if hasattr(obj, 'approved_date') and obj.approved_date:
            try:
                dt = datetime.strptime(obj.approved_date, "%Y-%m-%d %H:%M:%S")
                return dt.strftime("%d-%m-%Y %I:%M:%S %p")
            except:
                return str(obj.approved_date)
        return None
    
    def get_rejected_date_display(self, obj):
        """Format rejected datetime for display"""
        if hasattr(obj, 'rejected_date') and obj.rejected_date:
            try:
                dt = datetime.strptime(obj.rejected_date, "%Y-%m-%d %H:%M:%S")
                return dt.strftime("%d-%m-%Y %I:%M:%S %p")
            except:
                return str(obj.rejected_date)
        return None
    
    def validate_start_date(self, value):
        """Validate start date format"""
        if not is_valid_date_format(value):
            raise serializers.ValidationError(
                "Invalid date format. Use YYYY-MM-DD (e.g., 2025-01-27)"
            )
        return value
    
    def validate_end_date(self, value):
        """Validate end date format"""
        if not is_valid_date_format(value):
            raise serializers.ValidationError(
                "Invalid date format. Use YYYY-MM-DD (e.g., 2025-01-27)"
            )
        return value
    
    def validate(self, data):
        """Validate WFH request data"""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        # Validate date range
        if start_date and end_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d").date()
                end = datetime.strptime(end_date, "%Y-%m-%d").date()
                
                if end < start:
                    raise serializers.ValidationError({
                        "end_date": "End date cannot be before start date"
                    })
                
                # Check if dates are in the past
                current_date_str = get_current_date_ist()
                current_date = datetime.strptime(current_date_str, "%Y-%m-%d").date()
                
                if start < current_date:
                    raise serializers.ValidationError({
                        "start_date": "Cannot apply for WFH in the past"
                    })
            except ValueError as e:
                if "Invalid date format" not in str(e):
                    raise serializers.ValidationError({
                        "dates": "Invalid date format"
                    })
        
        return data
    
    def create(self, validated_data):
        """Create a new WFH request with IST timestamps"""
        request = self.context.get('request')
        
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("User must be authenticated")
        
        try:
            # Get employee instance for current user
            employee = Employee.objects.get(id=request.user.id)
        except Employee.DoesNotExist:
            raise serializers.ValidationError("Employee profile not found")
        
        # Calculate total days using your utility
        start_date = validated_data['start_date']
        end_date = validated_data['end_date']
        total_days = calculate_days_between(start_date, end_date)
        
        # Get current IST timestamp
        current_datetime = get_current_datetime_ist()
        
        # Create WFH instance
        wfh_request = WFH()
        wfh_request.employee = employee
        wfh_request.start_date = start_date
        wfh_request.end_date = end_date
        wfh_request.reason = validated_data.get('reason', '')
        wfh_request.remarks = validated_data.get('remarks', '')
        wfh_request.status = 'pending'
        wfh_request.total_days = total_days
        wfh_request.applied_date = current_datetime
        wfh_request.created_at = current_datetime
        wfh_request.updated_at = current_datetime
        
        # Set reporting manager if exists
        if hasattr(employee, 'reportingManager') and employee.reportingManager:
            wfh_request.reporting_manager = employee.reportingManager
            wfh_request.current_approver = employee.reportingManager
        
        # Save to database
        wfh_request.save()
        
        return wfh_request
    
    def update(self, instance, validated_data):
        """Update WFH request with IST timestamp"""
        # Update fields
        if 'start_date' in validated_data:
            instance.start_date = validated_data['start_date']
        
        if 'end_date' in validated_data:
            instance.end_date = validated_data['end_date']
        
        if 'reason' in validated_data:
            instance.reason = validated_data['reason']
        
        if 'remarks' in validated_data:
            instance.remarks = validated_data['remarks']
        
        # Recalculate total days if dates changed
        if 'start_date' in validated_data or 'end_date' in validated_data:
            instance.total_days = calculate_days_between(
                instance.start_date, 
                instance.end_date
            )
        
        # Update timestamp with IST
        instance.updated_at = get_current_datetime_ist()
        
        # Save
        instance.save()
        
        return instance 

# Alternative: Simple WFH List Serializer for cleaner list views
class WFHListSerializer(DocumentSerializer):
    """Simplified serializer for list views with expanded employee details"""
    
    employee_name = serializers.SerializerMethodField()
    employee_email = serializers.SerializerMethodField()
    employee_department = serializers.SerializerMethodField()
    reporting_manager_name = serializers.SerializerMethodField()
    approved_by_name = serializers.SerializerMethodField()
    
    # Display fields
    start_date_display = serializers.SerializerMethodField()
    end_date_display = serializers.SerializerMethodField()
    applied_date_display = serializers.SerializerMethodField()
    approved_date_display = serializers.SerializerMethodField()
    
    class Meta:
        model = WFH
        fields = [
            'id', 'start_date', 'end_date', 'total_days', 'reason', 
            'status', 'applied_date', 'approved_date', 'rejected_date',
            'rejection_reason', 'employee_name', 'employee_email', 
            'employee_department', 'reporting_manager_name', 'approved_by_name',
            'start_date_display', 'end_date_display', 'applied_date_display',
            'approved_date_display'
        ]
    
    def get_employee_name(self, obj):
        if obj.employee:
            return f"{obj.employee.firstName} {obj.employee.lastName}"
        return None
    
    def get_employee_email(self, obj):
        return obj.employee.email if obj.employee else None
    
    def get_employee_department(self, obj):
        if obj.employee and obj.employee.departmentId:
            return obj.employee.departmentId.deptName
        return None
    
    def get_reporting_manager_name(self, obj):
        if obj.reporting_manager:
            return f"{obj.reporting_manager.firstName} {obj.reporting_manager.lastName}"
        return None
    
    def get_approved_by_name(self, obj):
        if obj.approved_by:
            return f"{obj.approved_by.firstName} {obj.approved_by.lastName}"
        return None
    
    def get_start_date_display(self, obj):
        if obj.start_date:
            try:
                dt = datetime.strptime(obj.start_date, "%Y-%m-%d")
                return dt.strftime("%d-%m-%Y")
            except:
                return obj.start_date
        return None
    
    def get_end_date_display(self, obj):
        if obj.end_date:
            try:
                dt = datetime.strptime(obj.end_date, "%Y-%m-%d")
                return dt.strftime("%d-%m-%Y")
            except:
                return obj.end_date
        return None
    
    def get_applied_date_display(self, obj):
        if obj.applied_date:
            try:
                dt = datetime.strptime(obj.applied_date, "%Y-%m-%d %H:%M:%S")
                return dt.strftime("%d-%m-%Y %I:%M:%S %p")
            except:
                return obj.applied_date
        return None
    
    def get_approved_date_display(self, obj):
        if obj.approved_date:
            try:
                dt = datetime.strptime(obj.approved_date, "%Y-%m-%d %H:%M:%S")
                return dt.strftime("%d-%m-%Y %I:%M:%S %p")
            except:
                return obj.approved_date
        return None


#-----------------------------------------------------------------------Holiday Serializer------------------------------------------------------------------------------------
from .models import Holiday

class HolidaySerializer(serializers.Serializer):
    """Serializer for Holiday CRUD operations"""
    
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(max_length=200, required=True)
    date = serializers.CharField(required=True)  # "YYYY-MM-DD"
    holiday_type = serializers.ChoiceField(
        choices=['NATIONAL', 'REGIONAL', 'COMPANY', 'OPTIONAL', 'RESTRICTED'],
        default='COMPANY'
    )
    description = serializers.CharField(max_length=500, required=False, allow_blank=True)
    is_active = serializers.BooleanField(default=True)
    year = serializers.IntegerField(read_only=True)
    applicable_departments = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )
    applicable_locations = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )
    is_optional = serializers.BooleanField(default=False)
    max_optional_selections = serializers.IntegerField(default=0)
    created_by = serializers.CharField(read_only=True)
    created_at = serializers.CharField(read_only=True)
    updated_at = serializers.CharField(read_only=True)
    
    def validate_date(self, value):
        """Validate date format"""
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            raise serializers.ValidationError("Date must be in YYYY-MM-DD format")
    
    def create(self, validated_data):
        """Create new holiday"""
        holiday = Holiday(**validated_data)
        holiday.created_by = self.context.get('user_id', 'system')
        holiday.save()
        return holiday
    
    def update(self, instance, validated_data):
        """Update existing holiday"""
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance
    
    def to_representation(self, instance):
        """Convert MongoDB document to dict"""
        return {
            'id': str(instance.id),
            'name': instance.name,
            'date': instance.date,
            'holiday_type': instance.holiday_type,
            'description': instance.description or '',
            'is_active': instance.is_active,
            'year': instance.year,
            'applicable_departments': instance.applicable_departments or [],
            'applicable_locations': instance.applicable_locations or [],
            'is_optional': instance.is_optional,
            'max_optional_selections': instance.max_optional_selections,
            'created_by': instance.created_by or '',
            'created_at': instance.created_at or '',
            'updated_at': instance.updated_at or ''
        }