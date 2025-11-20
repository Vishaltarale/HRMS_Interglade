
from django.urls import path
from .import views

urlpatterns = [ 
    path("create/",views.create_shift,name="create_shift"),
    path('fetch/',views.list_shift,name="list_shift"),
    path("fetch/<str:pk>/",views.fetch_shift,name="fetch_shift"),
    path("update/<str:pk>/",views.update_shift,name="update_shift"),
    path("delete/<str:pk>/",views.delete_shift,name="delete_shift"),
]