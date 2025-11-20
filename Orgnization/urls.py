
from django.contrib import admin
from django.urls import path, include
from .import views

urlpatterns = [
    
    path("create/",views.create_org,name="create_org"),
    path('fetch/',views.list_org,name="list_org"),
    path("fetch/<str:pk>/",views.fetch_org,name="fetch_org"),
    path("update/<str:pk>/",views.update_org,name="update_org"),
    path("delete/<str:pk>/",views.delete_org,name="delete_org"),
]