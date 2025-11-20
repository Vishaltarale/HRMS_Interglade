from django.urls import path
from . import views   # correct way

urlpatterns = [
    path('students/', views.list_students, name='list-students'),          # GET all
    path('students/create/', views.create_student, name='create-student'), # POST
    path('students/<str:pk>/', views.get_student, name='get-student'),     # GET single
    path('students/update/<str:pk>/', views.update_student, name='update-student'), # PUT
    path('students/delete/<str:pk>/', views.delete_student, name='delete-student'), # DELETE

    #Employee
]