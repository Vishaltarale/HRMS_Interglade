
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/employee/', include('Employee.urls')),   
    path("api/organization/",include("Orgnization.urls")),
    path("api/department/",include('Departments.urls')),
    path("api/shifts/",include('Shifts.urls')),
    path("api/leave/",include("Leave.urls")),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

] 

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



#paro
#eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbXBJZCI6IjY5M2E5ZmNjYWQ2YTNjYjdlODFhY2Y1MyIsInJvbGUiOiJKUl9lbXBsb3llZSIsImlhdCI6MTc2Njk4NzUxNiwiZXhwIjoxNzY3NTkyMzE2fQ.Ewl58p4mKLGGWH5BVheu9TQ_rxFNd2X42hENvEMXB3g

#shivarj
#eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbXBJZCI6IjY5M2ZkNWFhN2EzOGJkMmM3YWNlMGNiNSIsInJvbGUiOiJTUl9lbXBsb3llZSIsImlhdCI6MTc2Njk4NzY3NCwiZXhwIjoxNzY3NTkyNDc0fQ.pm_4Qoba8vPa5lw_yRThIkBW3y1rBNwqMzg6yw96Gn0

#rohit
#eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbXBJZCI6IjY5MzkwY2EyNmRkNDE0ZmUxZThhMGJjOSIsInJvbGUiOiJKUl9lbXBsb3llZSIsImlhdCI6MTc2Njk4NzY5OSwiZXhwIjoxNzY3NTkyNDk5fQ.YsbDrF2Dh0FlJbNRmV9ZlePJFpk1_Erj-jXFYlFKr2k

#hr
#eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbXBJZCI6IjY5MzdlOWU1MTJhZjE2NDVhZTY0MmUzOCIsInJvbGUiOiJociIsImlhdCI6MTc2Njk4NzcyNCwiZXhwIjoxNzY3NTkyNTI0fQ.od7XvmttfUKk1LKaBPR6sUDae87eB8iXL2bWHw2Qamw

#omkar
#eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbXBJZCI6IjY5M2ZmZWQ2ZDU2ZjZiMmQxMWIwZmVlOCIsInJvbGUiOiJTUl9lbXBsb3llZSIsImlhdCI6MTc2Njk4Nzc0NSwiZXhwIjoxNzY3NTkyNTQ1fQ.UBXyXv8A2MACFZ_fJdONvQ1Y8fGmVOYipBzc0CS8Yf0