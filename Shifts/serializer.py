from rest_framework_mongoengine.serializers import DocumentSerializer
from Shifts.models import Shift


class ShiftSerializer(DocumentSerializer):
    class Meta:
        model = Shift
        fields = '__all__'