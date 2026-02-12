
from django.contrib import admin
from django.urls import path, include
from .import views
from Leave.views import *
from Leave.models import *

urlpatterns = [
    #for get all requests
    path("leaverequest/",views.LeaveRequestView.as_view(),name="LeaveRequest"),

    #for only percular employee can only see the his attendance
    path("leaverequest/<str:pk>/",views.EmpLeaveRequestView.as_view(),name="EmpLeaveRequestView"),

    #LeaveRequest Approveal Flow
    path("leaverequest/<str:pk>/approve/",views.LeaveApproveView.as_view(),name="LeaveApprove"),

    #LeaveRequest Rejection
    path("leaverequest/reject/<str:pk>/",LeaveRequestReject.as_view(),name="LeaveRequestReject"),

    #Request for Work From Home
    path("wfh/",OverallWorkFromHomeRequest.as_view(),name="OverallWorkFromHomeRequest"),
    path("wfh/<str:pk>/",EmployeeWorkFromHomeRequest.as_view(),name="WorkFromHomeRequest"),

    # Work From Home Approval Flow
    path("wfh/approve/<str:pk>/",WorkFromHomeApproveView.as_view(),name="WorkFromHomeApproveView"),
    path("wfh/reject/<str:pk>/",WorkFromHomeRejectView.as_view(),name="WorkFromHomeRejectView"),


     # Holiday CRUD
    path('holidays/', HolidayListCreateView.as_view(), name='holiday-list-create'),
    path('holidays/<str:holiday_id>/', HolidayDetailView.as_view(), name='holiday-detail'),
    
    # Calendar Integration
    path('calendar/holidays/', CalendarHolidaysView.as_view(), name='calendar-holidays'),
    
    # Bulk Operations
    path('holidays/bulk-upload/', BulkHolidayUploadView.as_view(), name='holiday-bulk-upload'),
    
]