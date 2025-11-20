from rest_framework_mongoengine.serializers import DocumentSerializer
from Orgnization.models import Organization

class OrgnizationSerializer(DocumentSerializer):
    class Meta:
        model = Organization
        fields = '__all__'


