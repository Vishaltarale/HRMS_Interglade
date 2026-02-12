from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import (
    CheckInView,
    CheckOutView,
    OverallAttendanceListView,
    EmpAttendanceListView,
    EmpAttendanceMarkView,
    EmpMarkAllView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [

    # ============================
    # Employee CRUD
    # ============================
    path("fetch/", views.list_emp, name="list_emp"),
    path("create/", views.create_emp, name="create_emp"),
    path("fetch/<str:pk>/", views.get_emp, name="get_emp"),
    path("update/<str:pk>/", views.update_emp, name="update_emp"),
    path("delete/<str:pk>/", views.delete_emp, name="delete_emp"),

    # ============================
    # Profile
    # ============================
    path("profile/", views.UserProfile, name="UserProfile"),
    path(
        "profiledata/",
        views.EmployeeProfileDataView.as_view(),
        name="employee_profile_data",
    ),

    # ============================
    # Auth & RBAC
    # ============================
    path("login/", views.login_emp, name="login_emp"),
    path("forgot-password/", views.forgot_password, name="forgot_password"),
    path("send_credentials/<str:pk>/", views.send_credentials, name="send_credentials"),
    path("logout/", views.logout_emp, name="logout_emp"),
    path("cleanup-blacklist/", views.cleanup_blacklist, name="cleanup_blacklist"),

    # ============================
    # Attendance
    # ORDER IS CRITICAL 🚨
    # ============================

    # Self / common
    path(
        "Attendance/today/",
        views.TodayAttendanceView.as_view(),
        name="today_attendance",
    ),
    path("checkin/", CheckInView.as_view(), name="checkin"),
    path("checkout/", CheckOutView.as_view(), name="checkout"),

    # HR / Admin
    path(
        "Attendance/overall/",
        OverallAttendanceListView.as_view(),
        name="overall_attendance",
    ),
    path(
        "Attendance/allmark/",
        EmpMarkAllView.as_view(),
        name="attendance_mark_all",
    ),
    path(
        "Attendance/mark/<str:pk>/",
        EmpAttendanceMarkView.as_view(),
        name="attendance_mark_single",
    ),

    # MUST BE LAST (dynamic)
    path(
        "Attendance/<str:pk>/",
        EmpAttendanceListView.as_view(),
        name="employee_attendance",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

#HRAccessToken -hr
#  eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbXBJZCI6IjY5MzdlOWU1MTJhZjE2NDVhZTY0MmUzOCIsInJvbGUiOiJociIsImV4cCI6MTc2NjY0MzYwNCwiaWF0IjoxNzY2MDM4ODA0fQ.Ck8tCcfP7yn_cDBRNlq5Rl0G5plrBt6syp6Cb-ukAjI 

#adminAccessToken - admin
#eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbXBJZCI6IjY5MzdlN2UwMTJhZjE2NDVhZTY0MmUzNiIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTc2NTk0OTMzMywiaWF0IjoxNzY1MzQ0NTMzfQ.o0efqe3ZjYPRejAIhJFVAGkhP-8KKuDtctglxh6j5VI

#SR_employee-shivraj 
# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbXBJZCI6IjY5M2ZkNWFhN2EzOGJkMmM3YWNlMGNiNSIsInJvbGUiOiJTUl9lbXBsb3llZSIsImV4cCI6MTc2NjM5NzE0NywiaWF0IjoxNzY1NzkyMzQ3fQ.HQt8zG7g7yoKU_IHiCYx-QAw2SBz9R7Bpsc8U9XnD6k

#emploteAccessToken-Rohit
#eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbXBJZCI6IjY5MzkwY2EyNmRkNDE0ZmUxZThhMGJjOSIsInJvbGUiOiJKUl9lbXBsb3llZSIsImV4cCI6MTc2NjcyNjcyNCwiaWF0IjoxNzY2MTIxOTI0fQ.tKoRTfHzSRc9-dFBjGr3_CNHmtag8dRvgX8V0k_-3CQ

#shreenathEMployeeAccessToken
#eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbXBJZCI6IjY5Mzk2NTMxNDg5MTYzNzEwY2Q1ZDM5ZiIsInJvbGUiOiJKUl9lbXBsb3llZSIsImV4cCI6MTc2NjEyMDk4NiwiaWF0IjoxNzY1NTE2MTg2fQ.H6d6aGz1mnVtmj2Blo2LsYsxBMeWeBZp4wFSLNI1lnw




# i am doing fuctionality for Attendance when user role is "hr",or "admin" is there then those have full autority to do all like checkin checkout ,see theres and other over all employees atendance also using url path("Attendance/overall/", OverallAttendanceListView.as_view()),

# they can mark attendance for single employee or all employee based on api for single employee mark attendance     path("Attendance/mark/<str:pk>/", EmpAttendanceMarkView.as_view(), name="AttendanceMark"),

# and for overall amek attenadance api as   path("Attendance/allmark/", EmpMarkAllView.as_view(), name="AttendanceMarkAll"),



# these work correct now still you check these 

# but actual conflict is near the 

# when user role is JR_rmployrr or SR_employee then 

# only logedin user data should be appear that we have to be fetched from the api

#     path("Attendance/<str:pk>/", EmpAttendanceListView.as_view(), name="EmpAttendance"),

# these call api service i wrote in employee_api_service.dart you can check there based above role based just call apis correctly







    # #Request for Work From Home
    # path("wfh/",OverallWorkFromHomeRequest.as_view(),name="OverallWorkFromHomeRequest"),
    # path("wfh/<str:pk>/",EmployeeWorkFromHomeRequest.as_view(),name="WorkFromHomeRequest"),



# from Leave.models import WFH
# from Leave.serializer import WFHSerializer
# # API END POINTS = api/Leave/wfh/<employee_id>/
# class EmployeeWorkFromHomeRequest(APIView):
#     """API for employees to request Work From Home (WFH)"""
#     def get(self, request, pk):
#         """Get all WFH requests for a specific employee"""
#         try:
#             employee = Employee.objects.get(id=pk)
#             wfh_requests = WFH.objects.filter(employee=employee)
#             serializer = WFHSerializer(wfh_requests, many=True)
            
#             return Response({
#                 "message": "All Work From Home Requests",
#                 "count": wfh_requests.count(),
#                 "result": serializer.data
#             })
            
#         except Exception as e:
#             import traceback
#             traceback.print_exc()
#             return Response({
#                 "error": f"An error occurred: {str(e)}"
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
#     def put(self, request, pk):
#         """Update a WFH request"""
#         try:
#             wfh_request = WFH.objects.get(id=pk)
#             serializer = WFHSerializer(wfh_request, data=request.data, partial=True, context={'request': request})
            
#             if serializer.is_valid():
#                 updated_wfh = serializer.save()
#                 return Response({
#                     "message": "WFH Request updated successfully",
#                     "data": WFHSerializer(updated_wfh).data
#                 })
            
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
#         except WFH.DoesNotExist:
#             return Response({
#                 "error": f"WFH Request with ID {pk} not found"
#             }, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             import traceback
#             traceback.print_exc()
#             return Response({
#                 "error": f"An error occurred: {str(e)}"
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
#     def delete(self, request, pk):
#         """Delete a WFH request"""
#         try:
#             wfh_request = WFH.objects.get(id=pk)
#             wfh_request.delete()
#             return Response({
#                 "message": "WFH Request Deleted Successfully"
#             }, status=status.HTTP_204_NO_CONTENT)
            
#         except WFH.DoesNotExist:
#             return Response({
#                 "error": f"WFH Request with ID {pk} not found"
#             }, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             import traceback
#             traceback.print_exc()
#             return Response({
#                 "error": f"An error occurred: {str(e)}"
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
# class OverallWorkFromHomeRequest(APIView):
#         def get(self, request):
            
#             """Get all WFH requests for the logged-in employee"""
#             try:
#                 # Get the employee by ID
#                 employee = Employee.objects.get(id=request.user.id)
                
#                 # Fetch WFH requests for this employee
#                 wfh_requests = WFH.objects.all()
#                 # Serialize the data
#                 serializer = WFHSerializer(wfh_requests, many=True)
                
#                 return Response({
#                     "message": "All Work From Home Requests",
#                     "count": wfh_requests.count(),
#                     "result": serializer.data
#                 })
                
#             except Employee.DoesNotExist:
#                 return Response({
#                     "error": "Employee profile not found"
#                 }, status=status.HTTP_404_NOT_FOUND)
#             except Exception as e:
#                 import traceback
#                 traceback.print_exc()
#                 return Response({
#                     "error": f"An error occurred: {str(e)}"
#                 }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
#         def post(self, request):
#             try:
#                 # Get the employee by ID
#                 employee = Employee.objects.get(id=request.user.id)
                
#                 # Prepare request data
#                 request_data = request.data.copy()
#                 request_data['employee'] = str(employee.id)  # Convert ObjectId to string for serializer
                
#                 # Serialize the WFH request
#                 serializer = WFHSerializer(data=request_data, context={'request': request})
                
#                 if serializer.is_valid():
#                     wfh_request = serializer.save()
                    
#                     return Response({
#                         "message": "Work From Home request created successfully",
#                         "request_id": str(wfh_request.id),
#                         "status": wfh_request.status,
#                         "details": WFHSerializer(wfh_request).data
#                     }, status=status.HTTP_201_CREATED)
                
#                 return Response({
#                     "error": "Validation failed",
#                     "details": serializer.errors
#                 }, status=status.HTTP_400_BAD_REQUEST)
                
#             except Employee.DoesNotExist:
#                 return Response({
#                     "error": "Employee profile not found"
#                 }, status=status.HTTP_404_NOT_FOUND)
#             except Exception as e:
#                 import traceback
#                 traceback.print_exc()
#                 return Response({
#                     "error": f"An error occurred: {str(e)}"
#                 }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
           