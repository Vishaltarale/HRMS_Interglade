
from django.urls import path
from .import views

urlpatterns = [ 
    path("create/",views.create_dept,name="create_dept"),
    path('fetch/',views.list_dept,name="list_dept"),
    path("fetch/<str:pk>/",views.fetch_dept,name="fetch_dept"),
    path("update/<str:pk>/",views.update_dept,name="update_dept"),
    path("delete/<str:pk>/",views.delete_dept,name="delete_dept"),
]