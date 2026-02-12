from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from Employee.models import Employee, Attendance, Documents
from Employee.serializer import EmployeeSerializer, AttendanceSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from HRMS.auth import MongoJWTAuthentication
from Employee.models import TokenBlacklist

from HRMS.permissions import IsAdmin, IsHR, IsSREmployee, IsJREmployee, IsAuthenticated, AllowAny

from datetime import datetime, timedelta
from django.conf import settings
import jwt
from bson import ObjectId
from django.core.mail import send_mail
from Departments.models import Departments
from Shifts.models import Shift
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from Orgnization.models import Organization
import os
import uuid
from mongoengine.errors import DoesNotExist, MultipleObjectsReturned
from datetime import date
from rest_framework.generics import ListAPIView
from utils.timezone_utils import (
    now, today, current_time,
    format_datetime_display, format_time_display, format_date_display,
    calculate_work_hours, calculate_work_duration_display,
    is_time_after, is_time_before,
    get_current_date_ist, get_current_time_ist, get_current_datetime_ist
)
import requests
from utils.pagination import CustomPagination
from utils.filters import apply_date_filters,apply_wfh_date_filters,apply_leave_date_filters

# ============================================================================
# EMPLOYEE CRUD OPERATIONS
# ============================================================================

#API END POINT = api/employee/fetch/
@api_view(["GET"])
@permission_classes([IsAuthenticated | IsHR | IsAdmin | IsSREmployee | IsJREmployee])
def list_emp(request):
    # Initialize paginator
    paginator = CustomPagination()
    
    # Get all employees
    employees = Employee.objects.all()
    
    # Apply pagination to the queryset
    paginated_employees = paginator.paginate_queryset(employees, request)
    
    # Serialize the paginated data
    serializer = EmployeeSerializer(paginated_employees, many=True)
    
    # Get additional data (not paginated)
    reporting_roles = ["admin", "hr", "SR_employee"]
    reporting_managers = Employee.objects.filter(
        role__in=reporting_roles
    ).only("id", "firstName")
    
    # Prepare the response data
    response_data = {
        "results": serializer.data,
        "organizations": [
            {"id": str(org.id), "orgName": org.orgName}
            for org in Organization.objects.only("orgName")
        ],
        "departments": [
            {"id": str(dept.id), "deptName": dept.deptName}
            for dept in Departments.objects.only("deptName")
        ],
        "shifts": [
            {"id": str(shift.id), "shiftType": shift.shiftType}
            for shift in Shift.objects.only("shiftType")
        ],
        "reporting_managers": [
            {
                "id": str(emp.id),
                "firstName": emp.firstName
            }
            for emp in reporting_managers
        ],
    }
    
    # Return paginated response
    return paginator.get_paginated_response(response_data)


DOCUMENT_FOLDERS = {
    'adharCard': '/media/documents/adhar/',
    'panCard': '/media/documents/pan/',
    'bankBook': '/media/documents/bank/',
    'xStandardMarksheet': '/media/documents/marksheets/10th/',
    'xiiStandardMarksheet': '/media/documents/marksheets/12th/',
    'degree': '/media/documents/degrees/',
    'experienceLetter': '/media/documents/experience/',
    'photo': '/media/photos/'
}


#API END POINT = api/employee/create/
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsHR | IsAdmin])
@parser_classes([MultiPartParser, FormParser])
def create_emp(request):
    print("=" * 80)
    print("INCOMING REQUEST DATA")
    print("=" * 80)
    
    # Helper function to restructure flattened data
    def restructure_flattened_data(flat_data):
        result = {}
        for key, value in flat_data.items():
            if '.' in key:
                parts = key.split('.')
                current = result
                for i, part in enumerate(parts):
                    if i == len(parts) - 1:
                        current[part] = value
                    else:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
            else:
                result[key] = value
        return result
    
    # Process text data
    text_data = {}
    for key, value in request.data.items():
        if key not in request.FILES:
            text_data[key] = value
    
    # Process file data
    file_data = {}
    for key, file in request.FILES.items():
        file_data[key] = file
    
    # Restructure both
    restructured_text = restructure_flattened_data(text_data)
    restructured_files = restructure_flattened_data(file_data)
    
    print("Text Data Structure:")
    for key, value in restructured_text.items():
        if isinstance(value, dict):
            print(f"{key}: {value}")
        else:
            print(f"{key}: {value}")
    
    print(f"📎 Files: {list(restructured_files.keys())}")
    print("=" * 80)
    
    # Validate text data
    serializer = EmployeeSerializer(data=restructured_text)
    
    if not serializer.is_valid():
        print("VALIDATION ERRORS:")
        for field, errors in serializer.errors.items():
            print(f"  {field}: {errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Create employee with text data
        employee = serializer.save()
        print(f"✅ Employee created with ID: {employee.id}")
        
        # Handle file uploads
        documents_data = {}
        
        if 'documents' in restructured_files:
            for doc_type, file_obj in restructured_files['documents'].items():
                if hasattr(file_obj, 'name') and doc_type in DOCUMENT_FOLDERS:
                    try:
                        # Get folder for this document type
                        folder = DOCUMENT_FOLDERS[doc_type]
                        
                        # Create folder if it doesn't exist
                        full_folder = os.path.join(settings.MEDIA_ROOT, folder)
                        os.makedirs(full_folder, exist_ok=True)
                        
                        # Generate unique filename
                        original_name = file_obj.name
                        name, ext = os.path.splitext(original_name)
                        
                        # Use employee ID and document type in filename
                        unique_name = f"{employee.id}_{doc_type}_{uuid.uuid4().hex[:6]}{ext}"
                        
                        # Remove any special characters
                        unique_name = "".join(c for c in unique_name if c.isalnum() or c in ['_', '.', '-'])
                        
                        # Full relative path
                        relative_path = os.path.join(folder, unique_name)
                        full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
                        
                        # Save file
                        with open(full_path, 'wb') as destination:
                            for chunk in file_obj.chunks():
                                destination.write(chunk)
                        
                        # Store relative path in documents data
                        documents_data[doc_type] = relative_path
                        
                        print(f"✅ Saved {doc_type}: {relative_path} ({file_obj.size} bytes)")
                        
                    except Exception as file_error:
                        print(f"❌ Error saving {doc_type}: {str(file_error)}")
                        continue
        
        # Update employee with document paths
        if documents_data:
            employee.documents = Documents(**documents_data)
            employee.save()
            print(f"📄 Documents saved: {list(documents_data.keys())}")
        else:
            print("⚠️  No documents saved")
        
        # Generate full URLs for response
        documents_with_urls = {}
        for doc_type, path in documents_data.items():
            if path:
                documents_with_urls[doc_type] = request.build_absolute_uri(settings.MEDIA_URL + path)
        
        print("=" * 80)
        
        return Response({
            "success": True,
            "message": "Employee created successfully",
            "employeeId": str(employee.id),
            "documents": documents_with_urls,
            "mediaRoot": settings.MEDIA_ROOT,
            "data": EmployeeSerializer(employee).data
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            "success": False,
            "error": str(e),
            "message": "Failed to create employee"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def get_employee_object(pk):
    try:
        return Employee.objects.get(id=ObjectId(pk))
    except Employee.DoesNotExist:
        return None


#API END POINT = api/employee/update/<emp-id>/
@api_view(['PUT', 'PATCH'])
@parser_classes([JSONParser, MultiPartParser, FormParser])  # CHANGED: Added JSONParser first
@permission_classes([IsAuthenticated, IsAdmin | IsHR])
def update_emp(request, pk):
    print("=" * 80)
    print("UPDATE EMPLOYEE REQUEST")
    print("=" * 80)
    
    # Get employee object
    emp = get_employee_object(pk)
    if not emp:
        return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)
    
    print(f"🔄 Updating employee ID: {emp.id}")
    print(f"👤 Current name: {emp.firstName} {emp.lastName}")
    print(f"📦 Content-Type: {request.content_type}")
    
    # Determine if this is a JSON request or multipart request
    is_json_request = 'application/json' in request.content_type
    has_files = bool(request.FILES)
    
    print(f"📝 Is JSON request: {is_json_request}")
    print(f"📎 Has files: {has_files}")
    
    # OPTION 1: Simple JSON update (no files)
    if is_json_request and not has_files:
        print("✅ Processing as JSON update")
        
        # Get data directly from request.data
        update_data = request.data.copy()
        
        print(f"📝 Update fields: {list(update_data.keys())}")
        
        # Validate with serializer (partial update)
        serializer = EmployeeSerializer(emp, data=update_data, partial=True)
        
        if not serializer.is_valid():
            print("❌ VALIDATION ERRORS:")
            for field, errors in serializer.errors.items():
                print(f"  {field}: {errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Save the employee data
            updated_employee = serializer.save()
            print(f"✅ Employee updated: {updated_employee.id}")
            print("=" * 80)
            
            return Response({
                "success": True,
                "message": "Employee updated successfully",
                "employeeId": str(updated_employee.id),
                "data": EmployeeSerializer(updated_employee).data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return Response({
                "success": False,
                "error": str(e),
                "message": "Failed to update employee"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # OPTION 2: Multipart update (with or without files)
    else:
        print("✅ Processing as multipart/form-data update")
        
        # Helper function to restructure flattened data
        def restructure_flattened_data(flat_data):
            result = {}
            for key, value in flat_data.items():
                if '.' in key:
                    parts = key.split('.')
                    current = result
                    for i, part in enumerate(parts):
                        if i == len(parts) - 1:
                            current[part] = value
                        else:
                            if part not in current:
                                current[part] = {}
                            current = current[part]
                else:
                    result[key] = value
            return result
        
        # Process text data
        text_data = {}
        for key, value in request.data.items():
            if key not in request.FILES:
                text_data[key] = value
        
        # Process file data
        file_data = {}
        for key, file in request.FILES.items():
            file_data[key] = file
        
        # Restructure both
        restructured_text = restructure_flattened_data(text_data)
        restructured_files = restructure_flattened_data(file_data)
        
        print("📝 Text Data Structure:")
        for key, value in restructured_text.items():
            if isinstance(value, dict):
                print(f"{key}: {value}")
            else:
                print(f"{key}: {value}")
        
        print(f"📎 Files to update: {list(restructured_files.keys())}")
        
        # Track existing documents for cleanup
        documents_to_delete = set()
        documents_data = {}
        
        # If we have new documents, we'll replace old ones
        if 'documents' in restructured_files:
            # Get current documents if they exist
            current_docs = {}
            if emp.documents:
                current_docs = emp.documents.__dict__
            
            # Mark current documents for deletion (if they exist on disk)
            for doc_type, doc_path in current_docs.items():
                if doc_path and doc_path != '' and os.path.exists(os.path.join(settings.MEDIA_ROOT, doc_path)):
                    documents_to_delete.add(doc_path)
                    print(f"🗑️  Marked for deletion: {doc_path}")
            
            # Handle new file uploads
            for doc_type, file_obj in restructured_files['documents'].items():
                if hasattr(file_obj, 'name') and doc_type in DOCUMENT_FOLDERS:
                    try:
                        # Get folder for this document type
                        folder = DOCUMENT_FOLDERS[doc_type]
                        
                        # Create folder if it doesn't exist
                        full_folder = os.path.join(settings.MEDIA_ROOT, folder)
                        os.makedirs(full_folder, exist_ok=True)
                        
                        # Generate unique filename
                        original_name = file_obj.name
                        name, ext = os.path.splitext(original_name)
                        
                        # Use employee ID and document type in filename
                        unique_name = f"{emp.id}_{doc_type}_{uuid.uuid4().hex[:6]}{ext}"
                        
                        # Remove any special characters
                        unique_name = "".join(c for c in unique_name if c.isalnum() or c in ['_', '.', '-'])
                        
                        # Full relative path
                        relative_path = os.path.join(folder, unique_name)
                        full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
                        
                        # Save file
                        with open(full_path, 'wb') as destination:
                            for chunk in file_obj.chunks():
                                destination.write(chunk)
                        
                        # Store relative path in documents data
                        documents_data[doc_type] = relative_path
                        
                        print(f"✅ Saved {doc_type}: {relative_path} ({file_obj.size} bytes)")
                        
                    except Exception as file_error:
                        print(f"❌ Error saving {doc_type}: {str(file_error)}")
                        continue
        
        # If we're updating documents via text data (paths), merge with uploaded files
        if 'documents' in restructured_text:
            for doc_type, doc_value in restructured_text['documents'].items():
                if doc_type not in documents_data:  # Don't override uploaded files
                    documents_data[doc_type] = doc_value
        
        # Remove documents that are being cleared (empty string or null)
        if 'documents' in restructured_text:
            for doc_type, doc_value in restructured_text['documents'].items():
                if doc_value in ['', None]:
                    # Check if this document exists in current documents
                    if emp.documents and hasattr(emp.documents, doc_type):
                        current_path = getattr(emp.documents, doc_type)
                        if current_path and current_path != '' and os.path.exists(os.path.join(settings.MEDIA_ROOT, current_path)):
                            documents_to_delete.add(current_path)
                            print(f"🗑️  Marked for deletion (cleared): {current_path}")
        
        # Update text data with merged documents
        if documents_data:
            restructured_text['documents'] = documents_data
        elif 'documents' in restructured_text:
            # Keep documents structure even if no files uploaded
            restructured_text['documents'] = restructured_text.get('documents', {})
        
        print("=" * 80)
        print("🔍 VALIDATING DATA...")
        
        # Validate with serializer (partial update)
        serializer = EmployeeSerializer(emp, data=restructured_text, partial=True)
        
        if not serializer.is_valid():
            print("❌ VALIDATION ERRORS:")
            for field, errors in serializer.errors.items():
                print(f"  {field}: {errors}")
            
            # Clean up any uploaded files if validation failed
            if documents_data:
                print("🧹 Cleaning up uploaded files due to validation error...")
                for doc_path in documents_data.values():
                    if doc_path and os.path.exists(os.path.join(settings.MEDIA_ROOT, doc_path)):
                        try:
                            os.remove(os.path.join(settings.MEDIA_ROOT, doc_path))
                            print(f"  ✅ Deleted: {doc_path}")
                        except Exception as e:
                            print(f"  ❌ Failed to delete {doc_path}: {e}")
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            print("✅ Validation successful")
            
            # Save the employee data
            updated_employee = serializer.save()
            print(f"✅ Employee updated: {updated_employee.id}")
            
            # Clean up old files that were replaced
            if documents_to_delete:
                print("🧹 Cleaning up old files...")
                for old_file_path in documents_to_delete:
                    full_path = os.path.join(settings.MEDIA_ROOT, old_file_path)
                    if os.path.exists(full_path):
                        try:
                            os.remove(full_path)
                            print(f"  ✅ Deleted old file: {old_file_path}")
                        except Exception as e:
                            print(f"  ⚠️  Warning: Could not delete {old_file_path}: {e}")
            
            # Generate full URLs for response
            documents_with_urls = {}
            if updated_employee.documents:
                doc_dict = updated_employee.documents.__dict__
                for doc_type, path in doc_dict.items():
                    if path and not doc_type.startswith('_'):  # Skip private attributes
                        documents_with_urls[doc_type] = request.build_absolute_uri(settings.MEDIA_URL + path)
            
            print("=" * 80)
            print("✅ UPDATE COMPLETE")
            print(f"📄 Documents: {list(documents_with_urls.keys())}")
            
            return Response({
                "success": True,
                "message": "Employee updated successfully",
                "employeeId": str(updated_employee.id),
                "documents": documents_with_urls,
                "data": EmployeeSerializer(updated_employee).data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Clean up any uploaded files if save failed
            if documents_data:
                print("🧹 Cleaning up uploaded files due to save error...")
                for doc_path in documents_data.values():
                    if doc_path and os.path.exists(os.path.join(settings.MEDIA_ROOT, doc_path)):
                        try:
                            os.remove(os.path.join(settings.MEDIA_ROOT, doc_path))
                            print(f"  ✅ Deleted: {doc_path}")
                        except Exception:
                            pass
            
            return Response({
                "success": False,
                "error": str(e),
                "message": "Failed to update employee"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



#API END POINT = api/employee/fetch/<emp-id>/
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsHR | IsAdmin | IsSREmployee | IsJREmployee])
def get_emp(request, pk):
    emp = get_employee_object(pk)
    if not emp:
        return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = EmployeeSerializer(emp)
    return Response({
        "data": serializer.data,
        "reporting_managers": [
            {"id": str(emp.id), "firstName": emp.firstName}
            for emp in Employee.objects.filter(role="SR_employee").only("id", "firstName")
        ],
    })

#API END POINT = api/employee/delete/<emp-id>/
@api_view(["DELETE"])
@permission_classes([IsAuthenticated, IsHR | IsAdmin])
def delete_emp(request, pk):
    emp = get_employee_object(pk)
    if not emp:
        return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)

    emp.delete()
    return Response({"message": "Employee deleted successfully"}, status=status.HTTP_200_OK)


# ____________________________________________________________________________Login ____________________________________________________________________________
# ============================================================================
# EMPLOYEE AUTHENTICATION
# ============================================================================
from datetime import datetime, timedelta, timezone
#API END POINT = api/employee/login/
@api_view(["POST"])
@permission_classes([AllowAny])
def login_emp(request):
    email = request.data.get("email")
    password = request.data.get("password")

    try:
        emp = Employee.objects.get(email=email)
    except Employee.DoesNotExist:
        return Response({"error": "Invalid email/password"}, status=401)

    if emp.password != password:
        return Response({"error": "Invalid email/password"}, status=401)

    # ✅ USE UTC TIME (timezone-aware)
    now_utc = datetime.now(timezone.utc)

    # Access token payload
    access_payload = {
        "empId": str(emp.id),
        "role": emp.role,
        "iat": now_utc,
        "exp": now_utc + timedelta(days=7),
    }

    access_token = jwt.encode(
        access_payload,
        settings.SECRET_KEY,
        algorithm="HS256"
    )

    # Refresh token payload
    refresh_payload = {
        "empId": str(emp.id),
        "type": "refresh",
        "iat": now_utc,
        "exp": now_utc + timedelta(days=30),
    }

    refresh_token = jwt.encode(
        refresh_payload,
        settings.SECRET_KEY,
        algorithm="HS256"
    )

    return Response({
        "accessToken": access_token,
        "refreshToken": refresh_token,
        "message": "Login successful",
        "empId": str(emp.id),
        "role": emp.role,
        "data": {
            "empId": str(emp.id),
            "name": f"{emp.firstName} {emp.lastName}",
            "email": emp.email,
            "role": emp.role
        },
        "isAuthenticated": True
    }, status=status.HTTP_200_OK)


#API END POINT = api/employee/logout/
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_emp(request):
    """
    Logout endpoint that blacklists both access and refresh tokens
    Request body should contain: { "refreshToken": "your_refresh_token_here" }
    """
    try:
        # Get access token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        access_token = auth_header.replace("Bearer ", "").strip() if auth_header else None
        
        # Get refresh token from request body
        refresh_token = request.data.get("refreshToken")
        
        blacklisted_count = 0
        current_datetime = get_current_datetime_ist()
        
        # Blacklist access token
        if access_token:
            try:
                payload = jwt.decode(
                    access_token, 
                    settings.SECRET_KEY, 
                    algorithms=["HS256"]
                )
                
                # Check if already blacklisted (MongoEngine query)
                if not TokenBlacklist.objects(token=access_token).first():
                    # Convert exp timestamp to IST string
                    exp_timestamp = payload.get("exp")
                    exp_datetime = datetime.fromtimestamp(exp_timestamp)
                    exp_ist = exp_datetime.strftime("%Y-%m-%d %H:%M:%S")
                    
                    TokenBlacklist(
                        token=access_token,
                        empId=payload.get("empId"),
                        expires_at=exp_ist,
                        blacklisted_at=current_datetime
                    ).save()
                    blacklisted_count += 1
                    
            except jwt.ExpiredSignatureError:
                # Token already expired, no need to blacklist
                pass
            except jwt.InvalidTokenError:
                # Invalid token, skip
                pass
            except Exception as e:
                print(f"Error blacklisting access token: {e}")
        
        # Blacklist refresh token
        if refresh_token:
            try:
                payload = jwt.decode(
                    refresh_token, 
                    settings.SECRET_KEY, 
                    algorithms=["HS256"]
                )
                
                # Check if already blacklisted (MongoEngine query)
                if not TokenBlacklist.objects(token=refresh_token).first():
                    # Convert exp timestamp to IST string
                    exp_timestamp = payload.get("exp")
                    exp_datetime = datetime.fromtimestamp(exp_timestamp)
                    exp_ist = exp_datetime.strftime("%Y-%m-%d %H:%M:%S")
                    
                    TokenBlacklist(
                        token=refresh_token,
                        empId=payload.get("empId"),
                        expires_at=exp_ist,
                        blacklisted_at=current_datetime
                    ).save()
                    blacklisted_count += 1
                    
            except jwt.ExpiredSignatureError:
                # Token already expired, no need to blacklist
                pass
            except jwt.InvalidTokenError:
                # Invalid token, skip
                pass
            except Exception as e:
                print(f"Error blacklisting refresh token: {e}")
        
        return Response({
            "message": "Logout successful",
            "isAuthenticated": False,
            "tokensInvalidated": blacklisted_count
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "error": "Logout failed",
            "details": str(e),
            "isAuthenticated": False
        }, status=status.HTTP_400_BAD_REQUEST)


#API END POINT = api/employee/cleanup-blacklist/
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cleanup_blacklist(request):
    """
    Admin endpoint to clean up expired tokens from blacklist
    """
    try:
        # Only allow admin to run this
        if request.user.role != "admin":
            return Response({
                "error": "Permission denied"
            }, status=status.HTTP_403_FORBIDDEN)
        
        current_datetime = get_current_datetime_ist()
        
        # Delete tokens that have expired (MongoEngine query)
        # Compare string dates
        deleted_count = TokenBlacklist.objects(
            expires_at__lt=current_datetime
        ).delete()
        
        return Response({
            "message": "Cleanup successful",
            "tokensRemoved": deleted_count
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "error": "Cleanup failed",
            "details": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# EMPLOYEE PROFILE & SETTINGS
# ============================================================================

#API END POINT = api/employee/send_credentials/<emp-id>/
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdmin | IsHR])
def send_credentials(request, pk):
    try:
        emp = Employee.objects.get(id=ObjectId(pk))
        print(emp.email)
    except Employee.DoesNotExist:
        return Response({"error": "Employee not found"}, status=404)
    
    subject = "Your HRMS Login Credentials"
    message = f"""
Hello,

Your HRMS account has been created successfully.

Login Details:
Email: {emp.email}
Password: {emp.password}

Please change your password after first login.

Thank You,
HRMS Team
"""
    from_email = settings.EMAIL_HOST_USER

    send_mail(
        subject,
        message,
        from_email,
        [emp.email],
        fail_silently=False,
    )

    return Response({
        "email": emp.email,
        "password": emp.password,
        "message": f"Email and password successfully sent to {emp.email}" 
    }, status=200)


#API END POINT = api/employee/change-password/

@api_view(["POST"])
@permission_classes([AllowAny])
def forgot_password(request):
    email = request.data.get("email")
    old_password = request.data.get("old_password")
    new_password = request.data.get("new_password")
    new_password_confirm = request.data.get("new_password_confirm")

    employee_present = Employee.objects.filter(email=email,password=old_password).first()

    if new_password != new_password_confirm:
        return Response({"error": "New passwords do not match"}, status=400)

    if employee_present:
        employee_present.password = new_password
        employee_present.save()
        return Response({"message": "Password changed successfully"}, status=200)
    else:
        return Response({"error": "Invalid Credentials"}, status=400)



#API END POINT = api/employee/profile/
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsHR | IsAdmin | IsSREmployee | IsJREmployee])
def UserProfile(request):
    try:
        emp_id = request.user.id
        emp_id_str = str(emp_id)
        
        employee = Employee.objects.get(id=emp_id)
        username = f"{employee.firstName}-{employee.lastName}"
        serializer = EmployeeSerializer(employee)
        
        # Handle department
        department_id = employee.departmentId
        if isinstance(department_id, ObjectId):
            department = Departments.objects.get(id=department_id).deptName
        else:
            department = employee.departmentId.deptName
        
        # Build base profile data
        profile_data = {
            "employee_id": emp_id_str,
            "username": username,
            "role": employee.role,
            "department": department,
            "employee": serializer.data,
        }
        
        # Add attendance data only for HR and Admin roles
        if employee.role.lower() in ["hr", "admin"]:
            # For HR/Admin - get all employees' attendance records
            attendance_queryset = Attendance.objects.all()
            attendance_queryset = apply_date_filters(attendance_queryset, request)

            # Calculate attendance statistics based on filtered queryset
            total_attendance_records = attendance_queryset.count()
            present_count = attendance_queryset.filter(status="present").count()    
            absent_count = attendance_queryset.filter(status="absent").count()
            on_time_count = attendance_queryset.filter(status="present", is_late=False).count()
            late_count = attendance_queryset.filter(is_late=True).count()
            half_day_count = attendance_queryset.filter(status="half_day").count()
            on_leave_count = attendance_queryset.filter(status="on_leave").count()
            wfh_count = attendance_queryset.filter(is_onWFH=True).count()

            # Calculate worked hours
            worked_hours = sum(
                att.total_work_hours 
                for att in attendance_queryset 
                if att.total_work_hours
            )
            
            # Calculate percentages (avoid division by zero)
            def safe_percentage(numerator, denominator):
                return round((numerator / denominator * 100), 2) if denominator > 0 else 0
            
            profile_data["attendance"] = {
                "total_records": total_attendance_records,
                "present_today": present_count,
                "present_percentage": safe_percentage(present_count, total_attendance_records),
                "absent_today": absent_count,
                "absent_percentage": safe_percentage(absent_count, total_attendance_records),
                "on_time_today": on_time_count,
                "on_time_percentage": safe_percentage(on_time_count, total_attendance_records),
                "late_today": late_count,
                "late_percentage": safe_percentage(late_count, total_attendance_records),
                "half_days": half_day_count,
                "worked_hours": worked_hours,
            }
            
            profile_data["filters_applied"] = {
                "date": request.query_params.get("date"),
                "month": request.query_params.get("month"),
                "year": request.query_params.get("year"),
            }
            
            # Add leaves data with on_leave and wfh for HR/Admin only
            if hasattr(employee, 'policy') and employee.policy:
                profile_data["leaves"] = {
                    "policy_name": employee.policy.policy_name,
                    "total": 18,
                    "used": 18 - int(employee.policy.earned_leave_days),
                    "available": int(employee.policy.earned_leave_days),
                    "leave_year_start_month": employee.policy.leave_year_start,
                    "leave_year_end_month": employee.policy.leave_year_end,
                    "on_leave": on_leave_count,
                    "wfh": wfh_count,
                    "half_day": half_day_count,
                }
        
        else:
            # For JR and SR employees - get only their attendance records
            attendance_queryset_employee = Attendance.objects.filter(employee=emp_id)
            attendance_queryset_employee = apply_date_filters(attendance_queryset_employee, request)
            
            # Calculate leave counts for this employee only
            on_leave_count = attendance_queryset_employee.filter(status="on_leave").count()
            wfh_count = attendance_queryset_employee.filter(is_onWFH=True).count()

            # For JR and SR employees - show leaves data with on_leave and wfh counts
            if hasattr(employee, 'policy') and employee.policy:
                profile_data["leaves"] = {
                    "policy_name": employee.policy.policy_name,
                    "total": 18,
                    "used": 18 - int(employee.policy.earned_leave_days),
                    "available": int(employee.policy.earned_leave_days),
                    "leave_year_start_month": employee.policy.leave_year_start,
                    "leave_year_end_month": employee.policy.leave_year_end,
                    "on_leave": on_leave_count,
                    "wfh": wfh_count,
                    "half_day": attendance_queryset_employee.filter(status="half_day").count(),
                }
        
        return Response({
            "statusCode": 200,
            "message": "Profile fetched successfully",
            "data": profile_data
        }, status=200)
    
    except Employee.DoesNotExist:
        return Response({
            "statusCode": 404,
            "message": "Employee not found",
            "error": "No employee found with the provided credentials"
        }, status=404)
    
    except Departments.DoesNotExist:
        return Response({
            "statusCode": 404,
            "message": "Department not found",
            "error": "Employee's department does not exist"
        }, status=404)
    
    except Exception as e:
        return Response({
            "statusCode": 500,
            "message": "Internal server error",
            "error": str(e)
        }, status=500)
    
#API END POINT = api/employee/dashboardData/
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsHR | IsAdmin | IsSREmployee | IsJREmployee])
def dashboardData(request):
    try:
        emp_id = request.user.id
        
        # Convert user.id if it is ObjectId
        emp_id_str = str(emp_id)
        employee = Employee.objects.get(id=emp_id)
        username = f"{employee.firstName}-{employee.lastName}"
        serializer = EmployeeSerializer(employee)
        dashboard_data = {
            "profile": {
                "employee_id": emp_id_str,
                "username": username,
                "role": employee.role,
                "employee": serializer.data,
            },
            "attendance": {
                "total_days": Attendance.objects(employee=employee).count(),
                "present_days": Attendance.objects(employee=employee, is_valid =True).count(),
                "absent_days": Attendance.objects(employee=employee, status="absent").count(),
                "late_days": Attendance.objects(employee=employee, is_late= True).count(),
                "half_days": Attendance.objects(employee=employee, status="half_day").count(),
                "worked_hours": sum(
                    att.total_work_hours for att in Attendance.objects(employee=employee) if att.total_work_hours
                ),
            },            
            
            "leaves": {
                "policy_name": employee.policy.policy_name,
                "total": int(18),
                "used": 18 - int(employee.policy.earned_leave_days),
                "available": int(employee.policy.earned_leave_days),
                "leave_year_start_month": employee.policy.leave_year_start,
                "leave_year_end_month": employee.policy.leave_year_end,
            }
        }
        return Response(dashboard_data)

    except Exception as e:
        return Response({"error": str(e)}, status=500)

# ============================================================================Attendance Check  AND CheckOut Views Logic =========================================================================
# ============================================================================
# ATTENDANCE VIEWS WITH STRING DATETIME STORAGE (IST)
# Storage: String in IST format
# Logic: Direct string comparisons
# Display: Already in IST, just format for display
# ============================================================================

class CheckInView(APIView):
    """
    Check-In API with string-based datetime storage (IST)
    - Stores date as "YYYY-MM-DD"
    - Stores time as "HH:MM:SS" in IST
    - All comparisons done with string times
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Get employee using MongoEngine
            employee = Employee.objects.get(id=request.user.id)
            
            if not employee.shiftId:
                return Response({"error": "No shift assigned"}, status=400)
            
            # Get current IST date and time as strings
            current_date_ist = get_current_date_ist()  # "YYYY-MM-DD"
            current_time_ist = get_current_time_ist()  # "HH:MM:SS"
            current_datetime_ist = get_current_datetime_ist()  # "YYYY-MM-DD HH:MM:SS"
            
            print(f"✅ Check-in date (IST): {current_date_ist}")
            print(f"✅ Check-in time (IST): {current_time_ist}")
            
            # Get or create attendance record for today (MongoEngine query)
            attendance = Attendance.objects(employee=employee, date=current_date_ist).first()

            if attendance.status == 'absent':
                return Response({
                    "error": "Cannot check in, marked absent for today"
                }, status=400)
            
            # FALLBACK: Create if doesn't exist
            if not attendance:
                print(f"⚠️  No attendance record found for {employee.firstName}, creating now...")
                attendance = Attendance(
                    employee=employee,
                    date=current_date_ist,
                    status='pending',
                    created_at=current_datetime_ist,
                    updated_at=current_datetime_ist
                )
            
            # Check if already checked in
            if attendance.check_in_time:
                return Response({
                    "error": "Already checked in today",
                    "check_in_time": format_time_display(attendance.check_in_time)
                }, status=400)
            
            # Extract location data
            location_data = self.extract_location_data(request)
            
            # Determine check-in status (compare time strings)
            attendance_status = self.determine_checkin_status(
                attendance,
                current_time_ist, 
                employee.shiftId.fromTime,
                employee.shiftId.lateMarkTime
            )
            print(f"✅ Check-in status: {attendance_status}")
            
            # Update attendance record (Store as string in IST)
            attendance.check_in_time = current_time_ist
            attendance.check_in_location = location_data.get('address', 'Unknown Location')
            attendance.check_in_device = self.detect_device_type(request)
            attendance.check_in_ip = self.get_client_ip(request)
            attendance.status = attendance_status
            attendance.updated_at = current_datetime_ist
            attendance.save()  # MongoEngine save
            
            # Return response (already in IST)
            return Response({
                "message": "Check-in successful",
                "status": attendance_status,
                "location": location_data.get('address', 'Unknown Location'),
                "check_in_time": format_time_display(current_time_ist),  # 12-hour format
                "check_in_date": format_date_display(current_date_ist),  # DD-MM-YYYY
                "check_in_datetime": format_datetime_display(current_datetime_ist),  # Full display
                "timezone": "Asia/Kolkata (IST)",
                "is_late": attendance.is_late,
                "latemark_time": format_time_display(employee.shiftId.lateMarkTime),
                "location_details": {
                    "address": location_data.get('address', 'Unknown Location'),
                    "latitude": location_data.get('latitude'),
                    "longitude": location_data.get('longitude'),
                    "accuracy": location_data.get('accuracy')
                }
            })
            
        except Employee.DoesNotExist:
            return Response({"error": "Employee not found"}, status=404)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=500)
    
    def extract_location_data(self, request):
        """Extract location from request with fallback to reverse geocoding"""
        data = request.data
        
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        address = (
            data.get('address') or 
            data.get('area') or 
            data.get('location') or 
            None
        )
        
        if latitude and longitude and not address:
            address = self.reverse_geocode(float(latitude), float(longitude))
        
        return {
            'address': address or 'Unknown Location',
            'latitude': float(latitude) if latitude else None,
            'longitude': float(longitude) if longitude else None,
            'accuracy': data.get('accuracy', 0)
        }
    
    def reverse_geocode(self, lat, lng):
        """Convert coordinates to area name using OpenStreetMap"""
        try:
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                'lat': lat,
                'lon': lng,
                'format': 'json',
                'addressdetails': 1
            }
            headers = {'User-Agent': 'HRMS-App/1.0'}
            
            response = requests.get(url, params=params, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                address_data = data.get('address', {})
                
                area = (
                    address_data.get('suburb') or
                    address_data.get('neighbourhood') or
                    address_data.get('city_district') or
                    address_data.get('village') or
                    address_data.get('town') or
                    address_data.get('city') or
                    None
                )
                
                if area:
                    city = address_data.get('city', 'Pune')
                    return f"{area}, {city}"
                
                return self.extract_area_from_address(data.get('display_name', ''))
        except Exception as e:
            print(f"❌ Reverse geocoding failed: {e}")
        
        return f"{lat}, {lng}"
    
    def extract_area_from_address(self, full_address):
        """Extract area name from full address"""
        known_areas = [
            'Wakad', 'Baner', 'Katraj', 'Tathawade', 'Thergaon', 'Hinjewadi',
            'Kothrud', 'Aundh', 'Viman Nagar', 'Koregaon Park', 'Hadapsar',
            'Magarpatta', 'Wagholi', 'Ravet', 'Akurdi', 'Nigdi', 'Chinchwad',
            'Pimple Saudagar', 'Bavdhan', 'Pashan', 'Sus', 'Mahalunge'
        ]
        
        parts = full_address.split(', ')
        
        for part in parts:
            for area in known_areas:
                if area.lower() in part.lower():
                    return area
        
        if len(parts) >= 4:
            return parts[3].strip()
        elif len(parts) >= 3:
            return parts[2].strip()
        
        return parts[0].strip() if parts else full_address

    def determine_checkin_status(self, attendance, checkin_time_str, from_time_str, late_mark_time_str):
        """
        Determine check-in status based on shift times (IST, 24-hour)

        Rules:
        - Before or at fromTime  → PRESENT (is_late = False)
        - After fromTime         → PRESENT (is_late = True)
        """
        print(f"🕐 Check-in time : {checkin_time_str}")
        print(f"🕐 Shift start   : {from_time_str}")
        print(f"🕐 Late mark     : {late_mark_time_str}")

        # If check-in is before or at shift start time
        if checkin_time_str <= from_time_str:
            if attendance.status == 'wfh':
                attendance.is_late = False
                attendance.is_onWFH = True
                attendance.save()
                print("✅ Status: PRESENT (On Time)")
                return "wfh"
            else:
                print("✅ Status: PRESENT (On Time)")
                attendance.is_late = False
                attendance.save()
                return "present"
        else:
            if attendance.status == 'wfh':
                attendance.is_late = True
                attendance.is_onWFH = True
                attendance.save()
                print("⚠️ Status: PRESENT (Late)")
                return "wfh"    
            else:
                # Check-in after shift start time
                print("⚠️ Status: PRESENT (Late)")
                attendance.is_late = True
                attendance.save()
                return "present"
    
    def detect_device_type(self, request):
        """Detect device type from request headers"""
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
            return 'mobile'
        elif 'tablet' in user_agent or 'ipad' in user_agent:
            return 'tablet'
        else:
            return 'desktop'
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CheckOutView(APIView):
    """
    Check-Out API with string-based datetime storage (IST)
    - Stores date as "YYYY-MM-DD"
    - Stores time as "HH:MM:SS" in IST
    - Calculates work hours from string times
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Get employee using MongoEngine
            employee = Employee.objects.get(id=request.user.id)
            
            # Get current IST date and time as strings
            current_date_ist = get_current_date_ist()  # "YYYY-MM-DD"
            current_time_ist = get_current_time_ist()  # "HH:MM:SS"
            current_datetime_ist = get_current_datetime_ist()  # "YYYY-MM-DD HH:MM:SS"
            
            print(f"✅ Check-out date (IST): {current_date_ist}")
            print(f"✅ Check-out time (IST): {current_time_ist}")
            
            # Get today's attendance record (MongoEngine query)
            attendance = Attendance.objects(employee=employee, date=current_date_ist).first()
            
            if not attendance or not attendance.check_in_time:
                return Response({
                    "error": "No check-in record found for today. Please check-in first."
                }, status=400)
            
            if attendance.check_out_time:
                return Response({
                    "error": "Already checked out today",
                    "check_out_time": format_time_display(attendance.check_out_time)
                }, status=400)
            
            # Extract location data
            location_data = self.extract_location_data(request)
            
            # Get check_in time (already string in IST)
            check_in_time_str = attendance.check_in_time
            
            print(f"🕐 Check-in time: {check_in_time_str}")
            print(f"🕐 Check-out time: {current_time_ist}")
            
            # Calculate work hours (using string times)
            work_hours = calculate_work_hours(check_in_time_str, current_time_ist, current_date_ist)
            work_duration_display = calculate_work_duration_display(check_in_time_str, current_time_ist)
            
            print(f"⏱️  Total work hours: {work_hours} hours ({work_duration_display})")
            
            # Determine final status based on work hours
            attendance_status = self.determine_status(work_hours,attendance)

            # Update attendance record (Store as string in IST)
            attendance.check_out_time = current_time_ist
            attendance.check_out_location = location_data.get('address', 'Unknown Location')
            attendance.check_out_device = self.detect_device_type(request)
            attendance.check_out_ip = self.get_client_ip(request)
            attendance.total_work_hours = work_hours
            attendance.status = attendance_status
            attendance.updated_at = current_datetime_ist
            attendance.save()  # MongoEngine save
            
            # Return response (already in IST)
            return Response({
                "message": "Check-out successful",
                "status": attendance_status,
                "location": location_data.get('address', 'Unknown Location'),
                "check_in_time": format_time_display(check_in_time_str),  # 12-hour format
                "check_out_time": format_time_display(current_time_ist),  # 12-hour format
                "check_out_date": format_date_display(current_date_ist),  # DD-MM-YYYY
                "check_out_datetime": format_datetime_display(current_datetime_ist),  # Full display
                "total_work_hours": work_hours,
                "work_duration": work_duration_display,
                "timezone": "Asia/Kolkata (IST)",
                "is_completed": True,
                "location_details": {
                    "address": location_data.get('address', 'Unknown Location'),
                    "latitude": location_data.get('latitude'),
                    "longitude": location_data.get('longitude'),
                    "accuracy": location_data.get('accuracy')
                }
            })
            
        except Employee.DoesNotExist:
            return Response({"error": "Employee not found"}, status=404)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=500)
    
    def extract_location_data(self, request):
        """Extract location from request with fallback to reverse geocoding"""
        data = request.data
        
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        address = (
            data.get('address') or 
            data.get('area') or 
            data.get('location') or 
            None
        )
        
        if latitude and longitude and not address:
            address = self.reverse_geocode(float(latitude), float(longitude))
        
        return {
            'address': address or 'Unknown Location',
            'latitude': float(latitude) if latitude else None,
            'longitude': float(longitude) if longitude else None,
            'accuracy': data.get('accuracy', 0)
        }
    
    def reverse_geocode(self, lat, lng):
        """Convert coordinates to area name using OpenStreetMap"""
        try:
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                'lat': lat,
                'lon': lng,
                'format': 'json',
                'addressdetails': 1
            }
            headers = {'User-Agent': 'HRMS-App/1.0'}
            
            response = requests.get(url, params=params, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                address_data = data.get('address', {})
                
                area = (
                    address_data.get('suburb') or
                    address_data.get('neighbourhood') or
                    address_data.get('city_district') or
                    address_data.get('village') or
                    address_data.get('town') or
                    address_data.get('city') or
                    None
                )
                
                if area:
                    city = address_data.get('city', 'Pune')
                    return f"{area}, {city}"
                
                return self.extract_area_from_address(data.get('display_name', ''))
        except Exception as e:
            print(f"❌ Reverse geocoding failed: {e}")
        
        return f"{lat}, {lng}"
    
    def extract_area_from_address(self, full_address):
        """Extract area name from full address"""
        known_areas = [
            'Wakad', 'Baner', 'Katraj', 'Tathawade', 'Thergaon', 'Hinjewadi',
            'Kothrud', 'Aundh', 'Viman Nagar', 'Koregaon Park', 'Hadapsar',
            'Magarpatta', 'Wagholi', 'Ravet', 'Akurdi', 'Nigdi', 'Chinchwad',
            'Pimple Saudagar', 'Bavdhan', 'Pashan', 'Sus', 'Mahalunge'
        ]
        
        parts = full_address.split(', ')
        
        for part in parts:
            for area in known_areas:
                if area.lower() in part.lower():
                    return area
        
        if len(parts) >= 4:
            return parts[3].strip()
        elif len(parts) >= 3:
            return parts[2].strip()
        
        return parts[0].strip() if parts else full_address

    def determine_status(self, work_hours, attendance):
        """
        Determine final attendance status based on total work hours
        
        Rules:
        - Less than 5 hours      → ABSENT
        - 5 to less than 9 hours → HALF_DAY
        - 9 hours or more        → PRESENT
        
        Note: is_late flag from check-in is preserved separately
        """
        print(f"📊 Calculating status: work_hours={work_hours}")
        
        if work_hours < 5:
            # Less than 5 hours = absent
            print("❌ Status: ABSENT (worked < 5 hours)")
            return "absent"
        elif work_hours >= 5 and work_hours < 9:
            # Between 5-9 hours = half day
            print("⚠️ Status: HALF_DAY (worked 5-9 hours)")
            return "half_day"
        else:
            # 9+ hours = present
            print("✅ Status: PRESENT (worked 9+ hours)")
            attendance.is_late = False  # Override late status if they worked full hours
            return "present"
    
    def detect_device_type(self, request):
        """Detect device type from request headers"""
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
            return 'mobile'
        elif 'tablet' in user_agent or 'ipad' in user_agent:
            return 'tablet'
        else:
            return 'desktop'
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


#============================================================================MarkAll and all Logic ===========================================================================
# ============================================================================
# ATTENDANCE LIST AND MANAGEMENT VIEWS
# ============================================================================

class TodayAttendanceView(APIView):
    """Get today's attendance for all employees (HR/Admin only)"""
    permission_classes = [IsAuthenticated, IsHR | IsAdmin]

    def get(self, request):
        try:
            employee = request.user
            today_date = get_current_date_ist()

            # Role check
            if employee.role not in ["hr", "admin"]:
                return Response(
                    {"error": "Permission denied"},
                    status=403
                )

            attendances = Attendance.objects.filter(date=today_date)

            serializer = AttendanceSerializer(attendances, many=True)
            return Response({
                "date": today_date,
                "present_count": attendances.filter(status="present").count(),
                "absent_count": attendances.filter(status="absent").count(),
                "half_day_count": attendances.filter(status="half_day").count(),
                "late_count": attendances.filter(is_late=True).count(),
                "on_time_count": attendances.filter(is_late=False, status="present").count(),
                "date_display": format_date_display(today_date),
                "count": attendances.count()
                # "todays_attendance": serializer.data
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {"error": str(e)},
                status=500
            )


from utils.attendance_filters import (
    apply_month_year_filter,
    apply_status_filter
)


class EmployeeProfileDataView(APIView):
    """Get employee profile data with attendance summary"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        emp_id = request.user.id

        if not emp_id:
            return Response({"error": "Invalid token"}, status=401)

        emp = Employee.objects.get(id=ObjectId(emp_id))

        qs = Attendance.objects(employee=emp.id)

        # ---- Apply Custom Filters ----
        qs = apply_month_year_filter(qs, request)
        qs = apply_status_filter(qs, request)

        # ---- Summary ----
        data = {
            "employee": {
                "id": str(emp.id),
                "name": emp.firstName + " " + emp.lastName,
                "role": emp.role,
                "department": emp.departmentId.deptName if emp.departmentId else None,
            },
            "summary": {
                "present": qs.filter(status="present").count(),
                "absent": qs.filter(status="absent").count(),
                "half_day": qs.filter(status="half_day").count(),
                "latemark": qs.filter(status="latemark").count(),
                "total_working_days": qs.count(),
                "total_hours_worked": sum(
                    att.total_work_hours or 0 for att in qs
                )
            }
        }

        return Response(data)


@permission_classes([IsAuthenticated, IsHR | IsAdmin])
class OverallAttendanceListView(ListAPIView):
    """Get overall attendance for all employees (HR/Admin only)"""
    pagination_class = CustomPagination
    
    def get(self, request):
        user = Employee.objects.get(id=request.user.id)

        if user.role == "hr" or user.role == "admin":
            # Get all attendance records
            attendance = Attendance.objects.all()
            
            # Apply date filters
            attendance = apply_date_filters(attendance, request)
            
            # Apply pagination
            paginated_attendance = self.paginate_queryset(attendance)
            
            # Serialize paginated data
            serializer = AttendanceSerializer(paginated_attendance, many=True)
            
            # Return paginated response
            return self.get_paginated_response(serializer.data)
        else:
            return Response({
                "message": f"{user.firstName}-{user.role} you don't have permission to do this"
            })



from Employee.models import Employee

class EmpAttendanceListView(ListAPIView):
    """Get attendance records for a specific employee"""
    serializer_class = AttendanceSerializer
    pagination_class = CustomPagination

    def get(self, request, pk):
        # Get attendance records for the specific employee
        queryset = Attendance.objects.filter(employee=pk)

        # Apply date filters
        queryset = apply_date_filters(queryset, request)

        # Get all employees list
        employees_list = [
            {"id": str(emp.id), "name": f"{emp.firstName} {emp.lastName}"}
            for emp in Employee.objects.only("id", "firstName", "lastName")
        ]

        # Check if no records found
        if queryset.count() == 0:
            return Response({
                "statusCode": 200,
                "message": "No attendance records found",
                "data": [],
                "meta": {
                    "total": 0,
                    "page": 1,
                    "pages": 0
                },
                "employees": employees_list
            })

        # Apply pagination
        paginated_queryset = self.paginate_queryset(queryset)
        
        # Serialize paginated data
        serializer = self.serializer_class(paginated_queryset, many=True)

        # Get paginated response
        response = self.get_paginated_response(serializer.data)
        
        # Add employees list to response
        response.data['employees'] = employees_list

        # Return paginated response with employees list
        return response

@permission_classes([IsAuthenticated, IsHR | IsAdmin])
class EmpAttendanceMarkView(APIView):
    """Mark/Validate attendance for an employee (HR/Admin only)"""
    def post(self, request, pk):
        try:
            user = Employee.objects.get(id=request.user.id)
            if user.role == "hr":
                if not ObjectId.is_valid(pk):
                    return Response(
                        {"error": "Invalid employee ID format"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                today_date = get_current_date_ist()

                attendance = Attendance.objects.get(id=pk)
                print(attendance.status)

                if attendance.is_valid:
                    return Response(
                        {
                            "message": f"Attendance already validated for {today_date} for employee {attendance.employee.firstName}"
                        },
                        status=status.HTTP_200_OK
                    )

                elif attendance.status in ["latemark", "present", "pending", "WFH", "half_day"]:
                    # Update status to present
                    attendance.is_valid = True
                    attendance.save()
                    
                    serializer = AttendanceSerializer(attendance)
                    return Response({
                        "message": "Attendance marked as present",
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        "message": f"Cannot change status from '{attendance.status}' to 'present'"
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    "message": f"{user.firstName}-{user.role} you don't have permission"
                }, status=status.HTTP_400_BAD_REQUEST)
        except DoesNotExist:
            # No attendance record found for today
            return Response(
                {"error": "No attendance record found for today. Please create one first."},
                status=status.HTTP_404_NOT_FOUND
            )
        except MultipleObjectsReturned:
            # Multiple attendance records for same day (shouldn't happen)
            return Response(
                {"error": "Multiple attendance records found for today"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@permission_classes([IsAuthenticated, IsHR | IsAdmin])
class EmpMarkAllView(ListAPIView):
    """Mark/Validate all attendance records based on date filters (HR/Admin only)"""
    serializer_class = AttendanceSerializer
    pagination_class = CustomPagination

    def post(self, request):
        """Validate attendance records for the filtered date/month/year"""
        user = Employee.objects.get(id=request.user.id)
        
        if user.role not in ["hr", "admin"]:
            return Response({
                "statusCode": 403,
                "message": f"{user.firstName}-{user.role} You don't have permission to do this"
            })
        
        # Get all attendance records
        attendances = Attendance.objects.all()
        
        # Check if date filters are provided
        date_param = request.query_params.get("date")
        month_param = request.query_params.get("month")
        year_param = request.query_params.get("year")
        
        # Apply date filters - if no filter, use today's date
        if not date_param and not month_param and not year_param:
            date_today = get_current_date_ist()
            attendances = attendances.filter(date=date_today)
            filter_description = f"today ({date_today})"
        else:
            attendances = apply_date_filters(attendances, request)
            if date_param:
                filter_description = f"date {date_param}"
            elif month_param and year_param:
                filter_description = f"month {month_param}/{year_param}"
            else:
                filter_description = "the selected period"
        
        # Check if any records found
        total_records = attendances.count()
        
        if total_records == 0:
            return Response({
                "statusCode": 200,
                "message": f"No attendance records found for {filter_description}"
            })
        
        # Check how many are already validated
        already_validated_count = attendances.filter(is_valid=True).count()
        
        # If all are already validated
        if already_validated_count == total_records:
            return Response({
                "statusCode": 200,
                "message": f"All {total_records} attendance records are already validated for {filter_description}"
            })
        
        # Mark all as validated (bulk update for better performance)
        updated_count = attendances.filter(is_valid=False).update(is_valid=True)
        
        return Response({
            "statusCode": 200,
            "message": f"Successfully validated attendance for {filter_description}",
            "data": {
                "total_records": total_records,
                "newly_validated": updated_count,
                "already_validated": already_validated_count,
                "filter_applied": filter_description
            }
        })
    
    def get(self, request):
        """Get attendance records for validation preview (with pagination)"""
        user = Employee.objects.get(id=request.user.id)
        
        if user.role not in ["hr", "admin"]:
            return Response({
                "statusCode": 403,
                "message": f"{user.firstName}-{user.role} You don't have permission to do this"
            })
        
        # Get all attendance records
        attendances = Attendance.objects.all()
        
        # Check if date filters are provided
        date_param = request.query_params.get("date")
        month_param = request.query_params.get("month")
        year_param = request.query_params.get("year")
        
        # Apply date filters - if no filter, use today's date
        if not date_param and not month_param and not year_param:
            date_today = get_current_date_ist()
            attendances = attendances.filter(date=date_today)
        else:
            attendances = apply_date_filters(attendances, request)
        
        # Check if no records found
        if attendances.count() == 0:
            return Response({
                "statusCode": 200,
                "message": "No attendance records found",
                "data": [],
                "meta": {
                    "total": 0,
                    "page": 1,
                    "pages": 0,
                    "validated_count": 0,
                    "pending_validation": 0
                }
            })
        
        # Get validation stats
        total_count = attendances.count()
        validated_count = attendances.filter(is_valid=True).count()
        pending_count = attendances.filter(is_valid=False).count()
        
        # Apply pagination
        paginated_queryset = self.paginate_queryset(attendances)
        
        # Serialize paginated data
        serializer = self.serializer_class(paginated_queryset, many=True)
        
        # Get the paginated response
        response = self.get_paginated_response(serializer.data)
        
        # Add validation stats to meta
        response.data['meta']['validated_count'] = validated_count
        response.data['meta']['pending_validation'] = pending_count
        
        return response
    
  