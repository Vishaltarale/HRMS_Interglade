from rest_framework_mongoengine.serializers import DocumentSerializer
from Departments.models import Departments


class DepartmentsSerializer(DocumentSerializer):
    class Meta:
        model = Departments
        fields = '__all__'