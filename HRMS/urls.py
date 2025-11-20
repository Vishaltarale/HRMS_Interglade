
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('Employee.urls')),   
    path("api/organization/",include("Orgnization.urls")),
    path("api/department/",include('Departments.urls')),
    path("api/shifts/",include('Shifts.urls')),

]