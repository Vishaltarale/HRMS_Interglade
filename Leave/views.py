from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from Leave.models import LeaveRequest
from Employee.models import Employee, Attendance, LeavePolicy
from Leave.serializer import LeaveSerializer
from rest_framework.generics import ListAPIView
from datetime import datetime, timedelta
from rest_framework import status as http_status
from utils.timezone_utils import (
    get_current_datetime_ist, 
    get_current_date_ist,
    format_date_display,
    format_datetime_display,
    compare_dates,
    get_date_range,
    calculate_days_between,
    is_valid_date_format
)

from utils.filters import apply_date_filters,apply_wfh_date_filters,apply_leave_date_filters
from utils.pagination import CustomPagination

# ============================================================================LEAVE CRUD ============================================================================
# API END POINTS = api/leave/leaverequest/
from utils.filters import apply_leave_date_filters
from utils.pagination import CustomPagination

from utils.filters import apply_leave_date_filters
from utils.pagination import CustomPagination
from datetime import datetime

class LeaveRequestView(APIView):
    def get(self, request):
        """
        Get leave requests based on user role with filters and pagination
        - HR/Admin: See all leave requests
        - SR_employee: See own + team's leave requests (where they are reporting manager)
        - JR_employee: See only own leave requests
        """
        try:
            # Get employee by email (Django user email should match Employee email)
            employee = Employee.objects.get(email=request.user.email)
            
            # Get reporting managers for response
            reporting_managers = [
                {"id": str(emp.id), "firstName": emp.firstName, "lastName": emp.lastName}
                for emp in Employee.objects.filter(role="SR_employee").only("id", "firstName", "lastName", "role")
            ]
            
            if employee.role in ["hr", "admin"]:
                # HR/Admin can see all leave requests
                leave_requests = LeaveRequest.objects.all()
                message = "All Employees Leave Requests"
                
            elif employee.role == "SR_employee":
                # SR employee can see:
                # 1. Their own leave requests
                # 2. Leave requests of employees who report to them
                
                # Get all employees who have this SR employee in their reportingManagers list
                team_employees = Employee.objects.filter(reportingManagers=employee)
                team_employee_ids = [emp.id for emp in team_employees]
                
                # Add SR employee's own ID
                team_employee_ids.append(employee.id)
                
                # Get leave requests for the team
                leave_requests = LeaveRequest.objects.filter(employee__in=team_employee_ids)
                message = f"{employee.firstName}'s Team Leave Requests"
                
            elif employee.role == "JR_employee":
                # JR employee can only see their own leave requests
                leave_requests = LeaveRequest.objects.filter(employee=employee)
                message = f"{employee.firstName}'s Leave Requests"
                
            else:
                # Unknown role
                return Response({
                    "error": f"Unknown role: {employee.role}"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Apply date filters
            leave_requests = apply_leave_date_filters(leave_requests, request)
            
            # Get employees on leave for the filtered date (if date filter is applied)
            employees_on_leave = []
            date_param = request.query_params.get("date")
            
            if date_param:
                # Get all approved leave requests that overlap with the specified date
                approved_leaves = LeaveRequest.objects.filter(
                    start_date__lte=date_param,
                    end_date__gte=date_param,
                    status='APPROVED'
                )
                
                # Build employee details list
                for leave in approved_leaves:
                    if leave.employee:
                        emp = leave.employee
                        employees_on_leave.append({
                            "employeeName": f"{emp.firstName} {emp.lastName}",
                            "leaveType": leave.leave_type,
                            "department": emp.departmentId.deptName if emp.departmentId else "N/A",
                            "startDate": leave.start_date,
                            "endDate": leave.end_date,
                            "totalDays": leave.total_days
                        })
            
            # Apply ordering for consistent pagination
            leave_requests = leave_requests.order_by('-start_date', '-applied_date')
            
            # Check if there are any leave requests after filtering
            if leave_requests.count() == 0:
                response_data = {
                    "statusCode": 200,
                    "message": message,
                    "role": employee.role,
                    "data": [],
                    "meta": {
                        "total": 0,
                        "page": 1,
                        "pages": 0
                    },
                    "reporting_managers": reporting_managers
                }
                
                # Add employees on leave info if date filter was applied
                if date_param:
                    response_data["employeesOnLeave"] = {
                        "date": date_param,
                        "count": len(employees_on_leave),
                        "employees": employees_on_leave
                    }
                
                return Response(response_data)
            
            # Apply pagination
            paginator = CustomPagination()
            paginated_requests = paginator.paginate_queryset(leave_requests, request, view=self)
            
            # Serialize the data
            serializer = LeaveSerializer(paginated_requests, many=True)
            
            # Return paginated response
            response = paginator.get_paginated_response(serializer.data)
            
            # Customize the response based on role
            response.data['message'] = message
            response.data['role'] = employee.role
            response.data['reporting_managers'] = reporting_managers
            
            # Add employees on leave info if date filter was applied
            if date_param:
                response.data['employeesOnLeave'] = {
                    "date": date_param,
                    "count": len(employees_on_leave),
                    "employees": employees_on_leave
                }
            
            # Add team_size for SR_employee
            if employee.role == "SR_employee":
                team_employees = Employee.objects.filter(reportingManagers=employee)
                response.data['team_size'] = team_employees.count()
            
            return response
                
        except Employee.DoesNotExist:
            return Response({
                "error": "Employee profile not found. Please contact HR."
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                "error": f"An error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Create a new leave request"""
        try:
            # Get employee by email
            employee = Employee.objects.get(email=request.user.email)
            
            # Add employee to request data
            request_data = request.data.copy()
            request_data['employee'] = str(employee.id)  # Convert ObjectId to string for serializer
            
            serializer = LeaveSerializer(data=request_data, context={'request': request})
            
            if serializer.is_valid():
                leave_request = serializer.save()
                
                # Format response with display dates
                response_data = LeaveSerializer(leave_request).data
                
                return Response({
                    "message": "Leave request created successfully",
                    "request_id": str(leave_request.id),
                    "status": leave_request.status,
                    "details": response_data
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                "error": "Validation failed",
                "details": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Employee.DoesNotExist:
            return Response({
                "error": "Employee profile not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                "error": f"An error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# API END POINTS = api/leave/leaverequest/<emp-id>/
from utils.filters import apply_leave_date_filters
from utils.pagination import CustomPagination

class EmpLeaveRequestView(APIView):
    
    def get(self, request, pk):
        """Get all leave requests for a specific employee with filters and pagination"""
        try:
            # First, get the employee to verify they exist
            employee = Employee.objects.get(id=pk)
            
            # Then get all leave requests for this employee
            leave_requests = LeaveRequest.objects.filter(employee=employee)
            
            # Apply date filters
            leave_requests = apply_leave_date_filters(leave_requests, request)
            
            # Apply ordering for consistent pagination
            leave_requests = leave_requests.order_by('-start_date', '-applied_date')
            
            # Check if there are any leave requests after filtering
            if leave_requests.count() == 0:
                return Response({
                    "statusCode": 200,
                    "message": f"No leave requests found for {employee.firstName} {employee.lastName}",
                    "data": [],
                    "meta": {
                        "total": 0,
                        "page": 1,
                        "pages": 0
                    },
                    "reporting_managers": [
                        {"id": str(emp.id), "firstName": emp.firstName, "lastName": emp.lastName}
                        for emp in Employee.objects.filter(role="SR_employee").only("id", "firstName", "lastName", "role")
                    ]
                })
            
            # Apply pagination
            paginator = CustomPagination()
            paginated_requests = paginator.paginate_queryset(leave_requests, request, view=self)
            
            # Serialize the data
            serializer = LeaveSerializer(paginated_requests, many=True)
            
            # Get reporting managers
            reporting_managers = [
                {"id": str(emp.id), "firstName": emp.firstName, "lastName": emp.lastName}
                for emp in Employee.objects.filter(role="SR_employee").only("id", "firstName", "lastName", "role")
            ]
            
            # Return paginated response
            response = paginator.get_paginated_response(serializer.data)
            # Customize the message and add reporting managers
            response.data['message'] = f"Leave Requests for {employee.firstName} {employee.lastName}"
            response.data['reporting_managers'] = reporting_managers
            
            return response
            
        except Employee.DoesNotExist:
            return Response({
                "error": f"Employee with ID {pk} not found"
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                "error": f"An error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def put(self, request, pk):
        """Update a leave request (only if not approved)"""
        try:
            leaverequest = LeaveRequest.objects.get(id=pk)
            
            # Check if already approved
            if leaverequest.status == "APPROVED":
                return Response({
                    "message": f"Your Leave-Request is now {leaverequest.status}, you can't modify",
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Use partial=True to allow partial updates
            serializer = LeaveSerializer(leaverequest, data=request.data, partial=True, context={'request': request})
            
            if serializer.is_valid():
                updated_leave = serializer.save()
                return Response({
                    "message": "Leave Request updated successfully",
                    "data": LeaveSerializer(updated_leave).data
                })
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except LeaveRequest.DoesNotExist:
            return Response({
                "error": f"Leave Request with ID {pk} not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                "error": f"An error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, pk):
        """Delete a leave request"""
        try:
            leaverequest = LeaveRequest.objects.get(id=pk)
            
            # Optional: Prevent deletion of approved leaves
            if leaverequest.status == "APPROVED":
                return Response({
                    "error": "Cannot delete an approved leave request. Please contact HR."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            leaverequest.delete()
            return Response({
                "message": "Leave Request Deleted Successfully"
            }, status=status.HTTP_204_NO_CONTENT)
            
        except LeaveRequest.DoesNotExist:
            return Response({
                "error": f"Leave Request with ID {pk} not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                "error": f"An error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ============================================================================# LEAVE APPROVAL FLOW ============================================================================
# API END POINTS = api/leave/approve/<LR-id>/
class LeaveApproveView(APIView):
    """
    Leave Approval API with IST string-based dates
    When approved, creates attendance records for entire leave period
    """

    def post(self, request, pk):
        try:
            # Get current user as employee
            emp = Employee.objects.get(id=request.user.id)
            
            print(f"📋 Approval Request from: {emp.firstName} {emp.lastName} ({emp.role})")
            
            # Check if user has approval rights
            if emp.role.lower() not in ["admin", "hr", "sr_employee"]:
                return Response(
                    {"message": f"{emp.firstName} you don't have approval access"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get leave request
            leaverequest = LeaveRequest.objects.get(id=pk)
            print(f"📝 Leave Request: {leaverequest.employee_name} - {leaverequest.leave_type}")
            
            # Check if leave is already processed
            if leaverequest.status != "PENDING":
                return Response(
                    {"message": f"Leave request is already {leaverequest.status.lower()}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get the employee who applied for leave
            employee = leaverequest.employee
            
            # Initialize policy if not exists
            if employee.policy is None:
                print("⚠️ Creating default policy for employee")
                employee.policy = LeavePolicy()
                employee.save()
            
            # Check probation period
            if leaverequest.is_on_probation and leaverequest.leave_type not in ["UPL", "Unpaid Leave"]:
                return Response(
                    {"message": "Employee is on probation. Only UPL (Unpaid Leave) is allowed."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check notice period for planned leaves
            if leaverequest.is_planned:
                notice_required = employee.policy.planned_notice_days
                
                # Calculate days until start using string dates
                try:
                    current_date_str = get_current_date_ist()
                    current_date = datetime.strptime(current_date_str, "%Y-%m-%d").date()
                    start_date = datetime.strptime(leaverequest.start_date, "%Y-%m-%d").date()
                    days_until_start = (start_date - current_date).days
                    
                    print(f"📅 Notice check: {days_until_start} days notice (required: {notice_required})")
                    
                    if days_until_start < notice_required:
                        return Response(
                            {"message": f"Planned leaves require {notice_required} days notice. Only {days_until_start} days given."},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                except Exception as e:
                    print(f"❌ Error calculating notice period: {str(e)}")
                    return Response(
                        {"message": f"Error calculating notice period: {str(e)}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Store current balances for response
            current_earned_balance = employee.policy.earned_leave_days
            current_special_balance = employee.policy.special_leave_days
            
            print(f"💰 Current Balance - Earned: {current_earned_balance}, Special: {current_special_balance}")
            
            # Approve based on leave type and deduct from balance
            if leaverequest.leave_type in ["PL", "Paid Leave", "SL", "Sick Leave"]:
                # Check if employee has sufficient earned leave balance
                if employee.policy.earned_leave_days >= leaverequest.total_days:
                    print(f"✅ Approving {leaverequest.leave_type} - Deducting {leaverequest.total_days} days")
                    
                    # Update policy
                    updated_policy = LeavePolicy(
                        policy_name=employee.policy.policy_name,
                        earned_leave_days=employee.policy.earned_leave_days - leaverequest.total_days,
                        earned_leave_monthly=employee.policy.earned_leave_monthly,
                        special_leave_days=employee.policy.special_leave_days,
                        planned_notice_days=employee.policy.planned_notice_days,
                        regular_notice_days=employee.policy.regular_notice_days,
                        approver_roles=employee.policy.approver_roles,
                        probation_days=employee.policy.probation_days,
                        leave_year_start=employee.policy.leave_year_start,
                        leave_year_end=employee.policy.leave_year_end,
                        is_active=employee.policy.is_active
                    )
                    employee.policy = updated_policy
                    employee.save()
                    
                    # Create attendance records for leave period
                    self.create_leave_attendance_records(employee, leaverequest)
                else:
                    return Response(
                        {"message": f"Insufficient earned leave balance. Available: {employee.policy.earned_leave_days} days, Requested: {leaverequest.total_days} days"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    
            elif leaverequest.leave_type in ["SPL", "Special Leave"]:
                # Check if employee has special leave available
                if employee.policy.special_leave_days >= leaverequest.total_days:
                    print(f"✅ Approving {leaverequest.leave_type} - Deducting {leaverequest.total_days} days")
                    
                    # Update policy
                    updated_policy = LeavePolicy(
                        policy_name=employee.policy.policy_name,
                        earned_leave_days=employee.policy.earned_leave_days,
                        earned_leave_monthly=employee.policy.earned_leave_monthly,
                        special_leave_days=employee.policy.special_leave_days - leaverequest.total_days,
                        planned_notice_days=employee.policy.planned_notice_days,
                        regular_notice_days=employee.policy.regular_notice_days,
                        approver_roles=employee.policy.approver_roles,
                        probation_days=employee.policy.probation_days,
                        leave_year_start=employee.policy.leave_year_start,
                        leave_year_end=employee.policy.leave_year_end,
                        is_active=employee.policy.is_active
                    )
                    employee.policy = updated_policy
                    employee.save()
                    
                    # Create attendance records for leave period
                    self.create_leave_attendance_records(employee, leaverequest)
                else:
                    return Response(
                        {"message": f"Insufficient special leave balance. Available: {employee.policy.special_leave_days} days, Requested: {leaverequest.total_days} days"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    
            elif leaverequest.leave_type in ["UPL", "Unpaid Leave"]:
                # No balance deduction for unpaid leave
                print(f"✅ Approving {leaverequest.leave_type} - No balance deduction")
                
                # Create attendance records for leave period
                self.create_leave_attendance_records(employee, leaverequest)
            else:
                return Response(
                    {"message": "Invalid leave type"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update leave request status with IST datetime
            current_datetime = get_current_datetime_ist()
            leaverequest.status = "APPROVED"
            leaverequest.current_approver = emp
            leaverequest.approved_by = emp
            leaverequest.approved_date = current_datetime
            leaverequest.updated_at = current_datetime
            leaverequest.save()
            
            print(f"✅ Leave request approved successfully at {current_datetime}")
            
            # Refresh employee object to get updated policy
            employee.reload()
            
            # Prepare response
            response_data = {
                "message": "Leave request approved successfully",
                "leave_id": str(leaverequest.id),
                "status": leaverequest.status,
                "approved_by": f"{emp.firstName} {emp.lastName}",
                "approved_date": format_datetime_display(current_datetime),
                "employee": {
                    "id": str(employee.id),
                    "name": f"{employee.firstName} {employee.lastName}",
                    "previous_balance": {
                        "earned_leave": current_earned_balance,
                        "special_leave": current_special_balance
                    },
                    "remaining_balance": {
                        "earned_leave": employee.policy.earned_leave_days,
                        "special_leave": employee.policy.special_leave_days
                    },
                    "policy_details": {
                        "policy_name": employee.policy.policy_name,
                        "earned_leave_monthly": employee.policy.earned_leave_monthly,
                        "planned_notice_days": employee.policy.planned_notice_days,
                        "regular_notice_days": employee.policy.regular_notice_days,
                        "probation_days": employee.policy.probation_days,
                        "leave_year_start": employee.policy.leave_year_start,
                        "leave_year_end": employee.policy.leave_year_end,
                        "is_active": employee.policy.is_active
                    }
                },
                "leave_details": {
                    "type": leaverequest.leave_type,
                    "days": leaverequest.total_days,
                    "start_date": format_date_display(leaverequest.start_date),
                    "end_date": format_date_display(leaverequest.end_date),
                    "reason": leaverequest.reason,
                    "is_planned": leaverequest.is_planned,
                    "is_emergency": leaverequest.is_emergency
                }
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except LeaveRequest.DoesNotExist:
            return Response(
                {"message": "Leave request not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Employee.DoesNotExist:
            return Response(
                {"message": "Employee not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {"message": f"Error approving leave: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def create_leave_attendance_records(self, employee, leaverequest):
        """
        Create attendance records for all days in the leave period
        Marks each day as 'on_leave' status
        Uses IST string-based dates
        """
        try:
            # Parse start and end dates
            start_date = datetime.strptime(leaverequest.start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(leaverequest.end_date, "%Y-%m-%d").date()
            
            # Get current datetime for audit fields
            current_datetime = get_current_datetime_ist()
            
            print(f"📅 Creating attendance records from {leaverequest.start_date} to {leaverequest.end_date}")
            
            # Iterate through each day in the leave period
            current_date = start_date
            created_count = 0
            updated_count = 0
            skipped_count = 0
            
            while current_date <= end_date:
                # Convert date to string format "YYYY-MM-DD"
                date_str = current_date.strftime("%Y-%m-%d")
                
                # Check if attendance record already exists
                attendance = Attendance.objects(employee=employee, date=date_str).first()
                
                if not attendance:
                    # Create new attendance record
                    print(f"✅ Creating attendance record for {employee.firstName} on {date_str}")
                    attendance = Attendance(
                        employee=employee,
                        date=date_str,
                        status='on_leave',
                        created_at=current_datetime,
                        updated_at=current_datetime
                    )
                    attendance.save()
                    created_count += 1
                else:
                    # Update existing record only if it's pending or absent
                    if attendance.status in ['pending', 'absent']:
                        print(f"🔄 Updating attendance record for {employee.firstName} on {date_str} (was: {attendance.status})")
                        attendance.status = 'on_leave'
                        attendance.updated_at = current_datetime
                        attendance.save()
                        updated_count += 1
                    else:
                        print(f"⏭️ Skipping {date_str} - already has status: {attendance.status}")
                        skipped_count += 1
                
                # Move to next day
                current_date += timedelta(days=1)
            
            print(f"📊 Leave attendance summary: {created_count} created, {updated_count} updated, {skipped_count} skipped")
            
        except Exception as e:
            print(f"❌ Error creating leave attendance records: {str(e)}")
            import traceback
            traceback.print_exc()


# ============================================================================
# LEAVE REJECTION FLOW
# ============================================================================
# API END POINTS = api/leave/reject/<LR-id>/
class LeaveRequestReject(APIView):
    """Leave rejection with IST datetime support"""
    
    def post(self, request, pk):
        """Reject a leave request - Step by Step Logic"""
        try:
            # Step 1: Get the current employee (rejector)
            rejector = Employee.objects.get(email=request.user.email)
            
            print(f"🚫 Rejection Request from: {rejector.firstName} {rejector.lastName} ({rejector.role})")
            
            # Step 2: Get the leave request
            leave_request = LeaveRequest.objects.get(id=pk)
            
            print(f"📝 Leave Request: {leave_request.employee_name} - {leave_request.leave_type}")
            
            # Step 3: Check if leave request is already approved
            if leave_request.status == "APPROVED":
                # Get HR info for message
                hr_employee = Employee.objects(role="hr").first()
                hr_name = f"{hr_employee.firstName} {hr_employee.lastName}" if hr_employee else "HR"
                return Response({
                    "error": f"Leave Request Already Approved. Please contact {hr_name} for changes."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Step 4: Check if leave request is already rejected
            if leave_request.status == "REJECTED":
                return Response({
                    "error": "Leave Request is already rejected"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Step 5: Check if leave request is already cancelled
            if leave_request.status == "CANCELLED":
                return Response({
                    "error": "Leave Request is already cancelled by employee"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Step 6: Validate that rejector has permission
            can_reject = False
            
            # Role-based permission check
            if rejector.role in ["admin", "hr"]:
                # Admin and HR can reject any pending leave request
                can_reject = True
                print("✅ Permission granted: Admin/HR")
            elif rejector.role == "SR_employee":
                # SR employee can reject if:
                # 1. They are the reporting manager of the requester
                if leave_request.reporting_manager and leave_request.reporting_manager.id == rejector.id:
                    can_reject = True
                    print("✅ Permission granted: Reporting Manager")
                # 2. They are assigned as current approver
                elif leave_request.current_approver and leave_request.current_approver.id == rejector.id:
                    can_reject = True
                    print("✅ Permission granted: Current Approver")
                # 3. They are in the employee's reportingManagers list
                elif leave_request.employee.reportingManagers and rejector in leave_request.employee.reportingManagers:
                    can_reject = True
                    print("✅ Permission granted: Employee's Reporting Manager")
            
            # Step 7: If no permission, return error
            if not can_reject:
                return Response({
                    "error": f"{rejector.role} - {rejector.firstName} doesn't have permission to reject this leave request"
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Step 8: Get rejection reason from request
            rejection_reason = request.data.get("reason", "").strip()
            if not rejection_reason:
                return Response({
                    "error": "Rejection reason is required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            print(f"📝 Rejection reason: {rejection_reason}")
            
            # Step 9: Update leave request with rejection details using IST datetime
            current_datetime = get_current_datetime_ist()
            leave_request.status = "REJECTED"
            leave_request.rejection_reason = rejection_reason
            leave_request.rejected_by = rejector
            leave_request.rejected_date = current_datetime
            leave_request.updated_at = current_datetime
            
            # Step 10: Save the changes
            leave_request.save()
            
            print(f"✅ Leave request rejected successfully at {current_datetime}")
            
            # Step 11: Return success response
            return Response({
                "message": "Leave Request Rejected Successfully",
                "details": {
                    "rejected_by": f"{rejector.firstName} {rejector.lastName}",
                    "rejection_reason": rejection_reason,
                    "rejected_date": format_datetime_display(current_datetime),
                    "employee_name": leave_request.employee_name,
                    "leave_dates": f"{format_date_display(leave_request.start_date)} to {format_date_display(leave_request.end_date)}",
                    "leave_type": leave_request.leave_type,
                    "total_days": leave_request.total_days
                }
            })
            
        except LeaveRequest.DoesNotExist:
            return Response({
                "error": "Leave request not found"
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Employee.DoesNotExist:
            return Response({
                "error": "Employee not found"
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                "error": f"An error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ============================================================================Request For Work Fro Home ============================================================================
from Leave.models import WFH
from Leave.serializer import WFHSerializer
# API END POINTS = api/Leave/wfh/<employee_id>/
from utils.filters import apply_wfh_date_filters
from utils.pagination import CustomPagination

class EmployeeWorkFromHomeRequest(APIView):
    """API for employees to request Work From Home (WFH)"""
    
    def get(self, request, pk):
        """Get all WFH requests for a specific employee with filters and pagination"""
        try:
            # Get the employee
            employee = Employee.objects.get(id=pk)
            
            # Fetch WFH requests for this employee
            wfh_requests = WFH.objects.filter(employee=employee.id)
            
            # Apply date filters (WFH-specific)
            wfh_requests = apply_wfh_date_filters(wfh_requests, request)
            
            # Apply ordering for consistent pagination
            wfh_requests = wfh_requests.order_by('-start_date', '-applied_date')
            
            # Apply pagination
            paginator = CustomPagination()
            paginated_requests = paginator.paginate_queryset(wfh_requests, request, view=self)
            
            # Serialize the data
            serializer = WFHSerializer(paginated_requests, many=True)
            
            # Return paginated response
            response = paginator.get_paginated_response(serializer.data)
            # Customize the message
            response.data['message'] = "All Work From Home Requests"
            
            return response
            
        except Employee.DoesNotExist:
            return Response({
                "error": "Employee not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                "error": f"An error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def put(self, request, pk):
        """Update a WFH request"""
        try:
            wfh_request = WFH.objects.get(id=pk)
            serializer = WFHSerializer(wfh_request, data=request.data, partial=True, context={'request': request})
            
            if serializer.is_valid():
                updated_wfh = serializer.save()
                return Response({
                    "message": "WFH Request updated successfully",
                    "data": WFHSerializer(updated_wfh).data
                })
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except WFH.DoesNotExist:
            return Response({
                "error": f"WFH Request with ID {pk} not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                "error": f"An error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, pk):
        """Delete a WFH request"""
        try:
            wfh_request = WFH.objects.get(id=pk)
            wfh_request.delete()
            return Response({
                "message": "WFH Request Deleted Successfully"
            }, status=status.HTTP_204_NO_CONTENT)
            
        except WFH.DoesNotExist:
            return Response({
                "error": f"WFH Request with ID {pk} not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                "error": f"An error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class OverallWorkFromHomeRequest(APIView):
    def get(self, request):
        """Get all WFH requests for the logged-in employee with filters and pagination"""
        try:
            # Get the employee by ID
            employee = Employee.objects.get(id=request.user.id)
            
            if employee.role not in ['SR_employee', 'admin', 'hr']:
                return Response({
                    "error": "You don't have the access to do these"
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Fetch WFH requests based on role
            if employee.role == 'SR_employee':
                wfh_requests = WFH.objects.filter(reporting_manager=employee.id)
            elif employee.role in ['admin', 'hr']:
                wfh_requests = WFH.objects.all()
            else:
                wfh_requests = WFH.objects.none()
            
            # Apply date filters
            wfh_requests = apply_wfh_date_filters(wfh_requests, request)
            
            # Get employees on WFH for the filtered date (if date filter is applied)
            employees_on_wfh = []
            date_param = request.query_params.get("date")
            
            if date_param:
                # Get all approved WFH requests that overlap with the specified date
                approved_wfh = WFH.objects.filter(
                    start_date__lte=date_param,
                    end_date__gte=date_param,
                    status='approved'
                )
                
                # Build employee details list
                for wfh in approved_wfh:
                    if wfh.employee:
                        emp = wfh.employee
                        employees_on_wfh.append({
                            "employeeName": f"{emp.firstName} {emp.lastName}",
                            "status": wfh.status,
                            "department": emp.departmentId.deptName if emp.departmentId else "N/A",
                            "startDate": wfh.start_date,
                            "endDate": wfh.end_date,
                            "totalDays": wfh.total_days,
                            "reason": wfh.reason
                        })
            
            # Apply ordering for consistent pagination
            wfh_requests = wfh_requests.order_by('-start_date', '-applied_date')
            
            # Check if there are any WFH requests after filtering
            if wfh_requests.count() == 0:
                response_data = {
                    "statusCode": 200,
                    "message": "All Work From Home Requests",
                    "data": [],
                    "meta": {
                        "total": 0,
                        "page": 1,
                        "pages": 0
                    }
                }
                
                # Add employees on WFH info if date filter was applied
                if date_param:
                    response_data["employeesOnWFH"] = {
                        "date": date_param,
                        "count": len(employees_on_wfh),
                        "employees": employees_on_wfh
                    }
                
                return Response(response_data)
            
            # Apply pagination
            paginator = CustomPagination()
            paginated_requests = paginator.paginate_queryset(wfh_requests, request, view=self)
            
            # Serialize the data
            serializer = WFHSerializer(paginated_requests, many=True)
            
            # Return paginated response
            response = paginator.get_paginated_response(serializer.data)
            print("data = ",response.data)
            # Customize the message
            response.data['message'] = "All Work From Home Requests"
            
            # Add employees on WFH info if date filter was applied
            if date_param:
                response.data['employeesOnWFH'] = {
                    "date": date_param,
                    "count": len(employees_on_wfh),
                    "employees": employees_on_wfh
                }
            
            return response
            
        except Employee.DoesNotExist:
            return Response({
                "error": "Employee profile not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                "error": f"An error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def post(self, request):
        try:
            # Create serializer with request context
            serializer = WFHSerializer(data=request.data, context={'request': request})
            
            if serializer.is_valid():
                wfh_request = serializer.save()
                
                return Response({
                    "message": "Work From Home request created successfully",
                    "request_id": str(wfh_request.id),
                    "status": wfh_request.status,
                    "details": WFHSerializer(wfh_request).data
                }, status=http_status.HTTP_201_CREATED)
            
            return Response({
                "error": "Validation failed",
                "details": serializer.errors
            }, status=http_status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                "error": f"An error occurred: {str(e)}"
            }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)


#---------------------------work from home approval flow-----------------------------==========================================================================================
# API END POINTS = api/leave/wfh/approve/<WFH-id>/
from Leave.models import WFH
from Leave.serializer import WFHSerializer
# API END POINTS = api/Leave/wfh/<employee_id>/
from utils.filters import apply_wfh_date_filters
from utils.pagination import CustomPagination

class EmployeeWorkFromHomeRequest(APIView):
    """API for employees to request Work From Home (WFH)"""
    
    def get(self, request, pk):
        """Get all WFH requests for a specific employee with filters and pagination"""
        try:
            # Get the employee
            employee = Employee.objects.get(id=pk)
            
            # Fetch WFH requests for this employee
            wfh_requests = WFH.objects.filter(employee=employee.id)
            
            # Apply date filters (WFH-specific)
            wfh_requests = apply_wfh_date_filters(wfh_requests, request)
            
            # Apply ordering for consistent pagination
            wfh_requests = wfh_requests.order_by('-start_date', '-applied_date')
            
            # Apply pagination
            paginator = CustomPagination()
            paginated_requests = paginator.paginate_queryset(wfh_requests, request, view=self)
            
            # Serialize the data
            serializer = WFHSerializer(paginated_requests, many=True)
            
            # Return paginated response
            response = paginator.get_paginated_response(serializer.data)
            # Customize the message
            response.data['message'] = "All Work From Home Requests"
            
            return response
            
        except Employee.DoesNotExist:
            return Response({
                "error": "Employee not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                "error": f"An error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def put(self, request, pk):
        """Update a WFH request"""
        try:
            wfh_request = WFH.objects.get(id=pk)
            serializer = WFHSerializer(wfh_request, data=request.data, partial=True, context={'request': request})
            
            if serializer.is_valid():
                updated_wfh = serializer.save()
                return Response({
                    "message": "WFH Request updated successfully",
                    "data": WFHSerializer(updated_wfh).data
                })
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except WFH.DoesNotExist:
            return Response({
                "error": f"WFH Request with ID {pk} not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                "error": f"An error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, pk):
        """Delete a WFH request"""
        try:
            wfh_request = WFH.objects.get(id=pk)
            wfh_request.delete()
            return Response({
                "message": "WFH Request Deleted Successfully"
            }, status=status.HTTP_204_NO_CONTENT)
            
        except WFH.DoesNotExist:
            return Response({
                "error": f"WFH Request with ID {pk} not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                "error": f"An error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
       

class OverallWorkFromHomeRequest(APIView):

    def get(self, request):
        """
        Get WFH requests based on employee role

        - HR/Admin: See all WFH requests
        - SR_employee: See own + team WFH requests
        - JR_employee: See only own WFH requests
        """

        try:
            # Get employee using email (same as Leave API)
            employee = Employee.objects.get(email=request.user.email)

            # ---------------- ROLE BASED DATA ---------------- #

            if employee.role in ["hr", "admin"]:
                wfh_requests = WFH.objects.all()
                message = "All Employees Work From Home Requests"

            elif employee.role == "SR_employee":

                # Get team employees
                team_employees = Employee.objects.filter(
                    reportingManagers=employee
                )

                team_employee_ids = [emp.id for emp in team_employees]

                # Add SR employee own ID
                team_employee_ids.append(employee.id)

                wfh_requests = WFH.objects.filter(
                    employee__in=team_employee_ids
                )

                message = f"{employee.firstName}'s Team Work From Home Requests"

            elif employee.role == "JR_employee":

                wfh_requests = WFH.objects.filter(employee=employee)

                message = f"{employee.firstName}'s Work From Home Requests"

            else:
                return Response({
                    "error": f"Unknown role: {employee.role}"
                }, status=status.HTTP_400_BAD_REQUEST)

            # ---------------- DATE FILTER ---------------- #
            wfh_requests = apply_wfh_date_filters(wfh_requests, request)

            # ---------------- EMPLOYEES ON WFH ---------------- #
            employees_on_wfh = []
            date_param = request.query_params.get("date")

            if date_param:
                approved_wfh = WFH.objects.filter(
                    start_date__lte=date_param,
                    end_date__gte=date_param,
                    status="approved"
                )

                for wfh in approved_wfh:
                    if wfh.employee:
                        emp = wfh.employee
                        employees_on_wfh.append({
                            "employeeName": f"{emp.firstName} {emp.lastName}",
                            "department": emp.departmentId.deptName if emp.departmentId else "N/A",
                            "startDate": wfh.start_date,
                            "endDate": wfh.end_date,
                            "totalDays": wfh.total_days,
                            "reason": wfh.reason
                        })

            # ---------------- ORDERING ---------------- #
            wfh_requests = wfh_requests.order_by(
                "-start_date", "-applied_date"
            )

            # ---------------- EMPTY DATA ---------------- #
            if wfh_requests.count() == 0:

                response_data = {
                    "statusCode": 200,
                    "message": message,
                    "role": employee.role,
                    "data": [],
                    "meta": {
                        "total": 0,
                        "page": 1,
                        "pages": 0
                    }
                }

                if date_param:
                    response_data["employeesOnWFH"] = {
                        "date": date_param,
                        "count": len(employees_on_wfh),
                        "employees": employees_on_wfh
                    }

                return Response(response_data)

            # ---------------- PAGINATION ---------------- #
            paginator = CustomPagination()
            paginated_requests = paginator.paginate_queryset(
                wfh_requests, request, view=self
            )

            serializer = WFHSerializer(paginated_requests, many=True)

            response = paginator.get_paginated_response(serializer.data)

            response.data["message"] = message
            response.data["role"] = employee.role

            if date_param:
                response.data["employeesOnWFH"] = {
                    "date": date_param,
                    "count": len(employees_on_wfh),
                    "employees": employees_on_wfh
                }

            # Add team size for SR employee
            if employee.role == "SR_employee":
                team_count = Employee.objects.filter(
                    reportingManagers=employee
                ).count()

                response.data["team_size"] = team_count

            return response

        except Employee.DoesNotExist:
            return Response({
                "error": "Employee profile not found"
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def post(self, request):
        try:
            # Create serializer with request context
            serializer = WFHSerializer(data=request.data, context={'request': request})
            
            if serializer.is_valid():
                wfh_request = serializer.save()
                
                return Response({
                    "message": "Work From Home request created successfully",
                    "request_id": str(wfh_request.id),
                    "status": wfh_request.status,
                    "details": WFHSerializer(wfh_request).data
                }, status=http_status.HTTP_201_CREATED)
            
            return Response({
                "error": "Validation failed",
                "details": serializer.errors
            }, status=http_status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                "error": f"An error occurred: {str(e)}"
            }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)


#---------------------------work from home approval flow-----------------------------==========================================================================================
# API END POINTS = api/leave/wfh/approve/<WFH-id>/
from datetime import datetime, timedelta
from Employee.models import Attendance  # Adjust import path based on your project structure
from utils.timezone_utils import get_current_datetime_ist, format_datetime_display, format_date_display

class WorkFromHomeApproveView(APIView):
    """Work From Home Approval API with Attendance Record Creation"""
    
    def post(self, request, pk):
        try:
            # Get current user as employee
            emp = Employee.objects.get(id=request.user.id)
            
            print(f"📋 WFH Approval Request from: {emp.firstName} {emp.lastName} ({emp.role})")
            
            # Check if user has approval rights
            if emp.role.lower() not in ["admin", "hr", "sr_employee"]:
                return Response(
                    {"message": f"{emp.firstName} you don't have approval access"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get WFH request
            wfh_request = WFH.objects.get(id=pk)
            print(f"📝 WFH Request: {wfh_request.employee.firstName} - {wfh_request.reason}")
            
            # Check if WFH is already processed
            if wfh_request.status != "pending":
                return Response(
                    {"message": f"WFH request is already {wfh_request.status.lower()}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get the employee who applied for WFH
            employee = wfh_request.employee
            
            # Additional permission check for SR_employee
            if emp.role == "SR_employee":
                # Check if the approver is in the employee's reportingManagers list
                if not employee.reportingManagers or emp not in employee.reportingManagers:
                    return Response(
                        {"message": f"{emp.firstName} doesn't have permission to approve this WFH request"},
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            # Approve WFH request
            current_datetime = get_current_datetime_ist()
            wfh_request.status = "approved"
            wfh_request.approved_by = emp
            wfh_request.approved_date = current_datetime
            wfh_request.updated_at = current_datetime
            wfh_request.save()
            
            print(f"✅ WFH request approved successfully at {current_datetime}")
            
            # Create attendance records for WFH period
            attendance_summary = self.create_wfh_attendance_records(employee, wfh_request)
            
            return Response({
                "message": "WFH request approved successfully",
                "wfh_id": str(wfh_request.id),
                "status": wfh_request.status,
                "approved_by": f"{emp.firstName} {emp.lastName}",
                "approved_date": format_datetime_display(current_datetime),
                "wfh_details": {
                    "employee": f"{employee.firstName} {employee.lastName}",
                    "start_date": format_date_display(wfh_request.start_date),
                    "end_date": format_date_display(wfh_request.end_date),
                    "total_days": wfh_request.total_days,
                    "reason": wfh_request.reason
                },
                "attendance_records": attendance_summary
            }, status=status.HTTP_200_OK)
            
        except WFH.DoesNotExist:
            return Response(
                {"message": "WFH request not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Employee.DoesNotExist:
            return Response(
                {"message": "Employee not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {"message": f"Error approving WFH: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def create_wfh_attendance_records(self, employee, wfh_request):
        """
        Create attendance records for all days in the WFH period
        Marks each day as 'wfh' status
        Uses IST string-based dates
        """
        try:
            # Parse start and end dates
            start_date = datetime.strptime(wfh_request.start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(wfh_request.end_date, "%Y-%m-%d").date()
            
            print(f"🔍 DEBUG: Start date: {start_date}, End date: {end_date}")
            print(f"🔍 DEBUG: Employee: {employee.firstName} {employee.lastName} (ID: {employee.id})")
            
            # Get current datetime for audit fields
            current_datetime = get_current_datetime_ist()
            
            print(f"📅 Creating WFH attendance records from {wfh_request.start_date} to {wfh_request.end_date}")
            
            # Iterate through each day in the WFH period
            current_date = start_date
            created_count = 0
            updated_count = 0
            skipped_count = 0
            
            while current_date <= end_date:
                # Convert date to string format "YYYY-MM-DD"
                date_str = current_date.strftime("%Y-%m-%d")
                
                # Check if attendance record already exists
                attendance = Attendance.objects(employee=employee, date=date_str).first()
                
                if not attendance:
                    # Create new attendance record
                    print(f"✅ Creating WFH attendance record for {employee.firstName} on {date_str}")
                    attendance = Attendance(
                        employee=employee,
                        date=date_str,
                        status='wfh',
                        is_onWFH=True,
                        created_at=current_datetime,
                        updated_at=current_datetime
                    )
                    attendance.save()
                    created_count += 1
                else:
                    # Update existing record only if it's pending or absent
                    if attendance.status in ['pending', 'absent']:
                        print(f"🔄 Updating attendance record for {employee.firstName} on {date_str} (was: {attendance.status})")
                        attendance.status = 'wfh'
                        attendance.is_onWFH = True
                        attendance.updated_at = current_datetime
                        attendance.save()
                        updated_count += 1
                    else:
                        print(f"⏭️ Skipping {date_str} - already has status: {attendance.status}")
                        skipped_count += 1
                
                # Move to next day
                current_date += timedelta(days=1)
            
            print(f"📊 WFH attendance summary: {created_count} created, {updated_count} updated, {skipped_count} skipped")
            
            return {
                "created": created_count,
                "updated": updated_count,
                "skipped": skipped_count,
                "total_days": int(wfh_request.total_days)
            }
            
        except Exception as e:
            print(f"❌ Error creating WFH attendance records: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "created": 0,
                "updated": 0,
                "skipped": 0,
                "error": str(e)
            }           
        
# API END POINTS = api/leave/wfh/reject/<WFH-id>/
class WorkFromHomeRejectView(APIView):
    def post(self, request, pk):
        """Reject a WFH request"""
        try:
            # Get the current employee (rejector)
            rejector = Employee.objects.get(email=request.user.email)
            
            print(f"🚫 WFH Rejection Request from: {rejector.firstName} {rejector.lastName} ({rejector.role})")
            
            # Get the WFH request
            wfh_request = WFH.objects.get(id=pk)
            
            print(f"📝 WFH Request: {wfh_request.employee.firstName} - {wfh_request.reason}")
            
            # Check if WFH request is already processed
            if wfh_request.status != "pending":
                return Response({
                    "message": f"WFH request is already {wfh_request.status.lower()}"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate that rejector has permission
            can_reject = False
            
            if rejector.role in ["admin", "hr"]:
                can_reject = True
                print("✅ Permission granted: Admin/HR")
            elif rejector.role == "SR_employee":
                # Check if the rejector is in the employee's reportingManagers list
                if wfh_request.employee.reportingManagers and rejector in wfh_request.employee.reportingManagers:
                    can_reject = True
                    print("✅ Permission granted: Reporting Manager")
            
            if not can_reject:
                return Response({
                    "error": f"{rejector.role} - {rejector.firstName} doesn't have permission to reject this WFH request"
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get rejection reason from request
            rejection_reason = request.data.get("reason", "").strip()
            if not rejection_reason:
                return Response({
                    "error": "Rejection reason is required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            print(f"📝 Rejection reason: {rejection_reason}")
            
            # Update WFH request with rejection details using IST datetime
            current_datetime = get_current_datetime_ist()
            wfh_request.status = "rejected"
            wfh_request.rejection_reason = rejection_reason
            wfh_request.rejected_by = rejector
            wfh_request.rejected_date = current_datetime
            wfh_request.updated_at = current_datetime
            wfh_request.save()
            
            print(f"✅ WFH request rejected successfully at {current_datetime}")
            
            # Return success response
            return Response({
                "message": "WFH Request Rejected Successfully",
                "details": {
                    "rejected_by": f"{rejector.firstName} {rejector.lastName}",
                    "rejection_reason": rejection_reason,
                    "rejected_date": format_datetime_display(current_datetime),
                    "employee_name": f"{wfh_request.employee.firstName} {wfh_request.employee.lastName}",
                    "wfh_dates": f"{format_date_display(wfh_request.start_date)} to {format_date_display(wfh_request.end_date)}",
                    "reason": wfh_request.reason
                }
            })
        except WFH.DoesNotExist:
            return Response({
                "error": "WFH request not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Employee.DoesNotExist:
            return Response({
                "error": "Employee not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                "error": f"An error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            # Optional: Log the error or perform cleanup
            pass

# ============================================================================Holiday Management ============================================================================
# API END POINTS = api/leave/holiday/<employee_id>/
# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Holiday
from Leave.serializer import HolidaySerializer
from datetime import datetime

class HolidayListCreateView(APIView):
    """
    GET: List all holidays (with filters)
    POST: Create new holiday (HR only)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all holidays with optional filters"""
        try:
            # Get query parameters
            year = request.query_params.get('year')
            holiday_type = request.query_params.get('type')
            is_active = request.query_params.get('is_active', 'true')
            month = request.query_params.get('month')
            
            # Build query
            query = {}
            
            if year:
                query['year'] = int(year)
            else:
                # Default to current year
                query['year'] = datetime.utcnow().year
            
            if holiday_type:
                query['holiday_type'] = holiday_type.upper()
            
            if is_active.lower() == 'true':
                query['is_active'] = True
            
            # Month filter (if provided)
            if month:
                # Filter dates by month
                holidays = Holiday.objects(**query)
                holidays = [
                    h for h in holidays 
                    if datetime.strptime(h.date, "%Y-%m-%d").month == int(month)
                ]
            else:
                holidays = Holiday.objects(**query)
            
            serializer = HolidaySerializer(holidays, many=True)
            
            return Response({
                'success': True,
                'count': len(serializer.data),
                'holidays': serializer.data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def post(self, request):
        """Create new holiday (HR only)"""
        try:
            print("role =", request.user.role)
            emp = Employee.objects.get(id=request.user.id)
            print("emp.role =", emp.role)
            # Check if user is HR
            if emp.role not in ['hr', 'admin']:
                return Response({
                    'success': False,
                    'error': 'Only HR can create holidays'
                }, status=status.HTTP_403_FORBIDDEN)
            
            serializer = HolidaySerializer(
                data=request.data,
                context={'user_id': str(request.user.id)}
            )
            
            if serializer.is_valid():
                holiday = serializer.save()
                return Response({
                    'success': True,
                    'message': 'Holiday created successfully',
                    'holiday': HolidaySerializer(holiday).data
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class HolidayDetailView(APIView):
    """
    GET: Get single holiday
    PUT: Update holiday (HR only)
    DELETE: Delete holiday (HR only)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, holiday_id):
        """Get single holiday details"""
        try:
            holiday = Holiday.objects.get(id=holiday_id)
            serializer = HolidaySerializer(holiday)
            
            return Response({
                'success': True,
                'holiday': serializer.data
            }, status=status.HTTP_200_OK)
        
        except Holiday.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Holiday not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request, holiday_id):
        """Update holiday (HR only)"""
        try:
            emp = Employee.objects.get(id=request.user.id)
            # Check if user is HR
            if emp.role not in ['hr', 'admin']:
                return Response({
                    'success': False,
                    'error': 'Only HR can update holidays'
                }, status=status.HTTP_403_FORBIDDEN)
            
            holiday = Holiday.objects.get(id=holiday_id)
            serializer = HolidaySerializer(holiday, data=request.data, partial=True)
            
            if serializer.is_valid():
                updated_holiday = serializer.save()
                return Response({
                    'success': True,
                    'message': 'Holiday updated successfully',
                    'holiday': HolidaySerializer(updated_holiday).data
                }, status=status.HTTP_200_OK)
            
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Holiday.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Holiday not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, holiday_id):
        """Delete holiday (HR only)"""
        try:
            emp = Employee.objects.get(id=request.user.id)
            # Check if user is HR
            if emp.role not in ['hr', 'admin']:
                return Response({
                    'success': False,
                    'error': 'Only HR can delete holidays'
                }, status=status.HTTP_403_FORBIDDEN)
            
            holiday = Holiday.objects.get(id=holiday_id)
            holiday_name = holiday.name
            holiday.delete()
            
            return Response({
                'success': True,
                'message': f'Holiday "{holiday_name}" deleted successfully'
            }, status=status.HTTP_200_OK)
        
        except Holiday.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Holiday not found'
            }, status=status.HTTP_404_NOT_FOUND)
    


class CalendarHolidaysView(APIView):
    """
    GET: Get holidays for calendar view
    Returns holidays formatted for calendar display
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get holidays formatted for calendar"""
        try:
            year = request.query_params.get('year', datetime.utcnow().year)
            month = request.query_params.get('month')
            
            query = {'year': int(year), 'is_active': True}
            holidays = Holiday.objects(**query)
            
            # Filter by employee's department/location
            employee = request.user.id  # Assuming user has employee reference
            applicable_holidays = [
                h for h in holidays 
                if h.is_applicable_to_employee(employee)
            ]
            
            # Filter by month if provided
            if month:
                applicable_holidays = [
                    h for h in applicable_holidays
                    if datetime.strptime(h.date, "%Y-%m-%d").month == int(month)
                ]
            
            # Format for calendar
            calendar_events = []
            for holiday in applicable_holidays:
                calendar_events.append({
                    'id': str(holiday.id),
                    'title': holiday.name,
                    'date': holiday.date,
                    'type': 'holiday',
                    'holiday_type': holiday.holiday_type,
                    'description': holiday.description or '',
                    'is_optional': holiday.is_optional,
                    'color': self.get_holiday_color(holiday.holiday_type)
                })
            
            return Response({
                'success': True,
                'count': len(calendar_events),
                'events': calendar_events
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def get_holiday_color(self, holiday_type):
        """Get color code for calendar based on holiday type"""
        colors = {
            'NATIONAL': '#FF5252',  # Red
            'REGIONAL': '#FF9800',  # Orange
            'COMPANY': '#2196F3',   # Blue
            'OPTIONAL': '#4CAF50',  # Green
            'RESTRICTED': '#9E9E9E' # Grey
        }
        return colors.get(holiday_type, '#2196F3')


class BulkHolidayUploadView(APIView):
    """
    POST: Bulk upload holidays from CSV/Excel
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Upload holidays in bulk"""
        try:
            emp = Employee.objects.get(id=request.user.id)
            # Check if user is HR
            if emp.role not in ['hr', 'admin']:
                return Response({
                    'success': False,
                    'error': 'Only HR can upload holidays'
                }, status=status.HTTP_403_FORBIDDEN)
            
            holidays_data = request.data.get('holidays', [])
            
            created_holidays = []
            errors = []
            
            for idx, holiday_data in enumerate(holidays_data):
                try:
                    serializer = HolidaySerializer(
                        data=holiday_data,
                        context={'user_id': str(request.user.id)}
                    )
                    
                    if serializer.is_valid():
                        holiday = serializer.save()
                        created_holidays.append(HolidaySerializer(holiday).data)
                    else:
                        errors.append({
                            'row': idx + 1,
                            'errors': serializer.errors
                        })
                except Exception as e:
                    errors.append({
                        'row': idx + 1,
                        'error': str(e)
                    })
            
            return Response({
                'success': True,
                'created_count': len(created_holidays),
                'error_count': len(errors),
                'holidays': created_holidays,
                'errors': errors
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)