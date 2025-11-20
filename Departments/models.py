from mongoengine import Document, StringField, ReferenceField, CASCADE
from Orgnization.models import Organization


class Departments(Document):
    deptName = StringField(required=True, max_length=50)
    deptCode = StringField(required=True, max_length=100, unique=True)
    deptDesc = StringField(required=True, max_length=200)
    orgId = ReferenceField(Organization, reverse_delete_rule=CASCADE, required=True)
    orgStatus = StringField(required=True, choices=["Active", "Inactive"])

    meta = {
        'collection': 'departments',
        'indexes': [
            'deptCode',
            'deptName',
            {
                'fields': ['orgId']
            }
        ]
    }
