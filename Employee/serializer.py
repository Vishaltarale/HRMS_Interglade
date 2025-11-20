from rest_framework_mongoengine.serializers import DocumentSerializer
from .models import Student,Employee

class StudentSerializer(DocumentSerializer):
    class Meta:
        model = Student
        fields = '__all__'


class EmployeeSerializer(DocumentSerializer):
    class Meta:
        model = Employee
        fields = '__all__'