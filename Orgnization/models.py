from mongoengine import Document, StringField, EmailField, URLField

class Organization(Document):
    orgName = StringField(required=True, max_length=50)
    orgLocation = StringField(required=True, max_length=100)
    orgContact = StringField(required=True, max_length=100)  # Only digits, 10–12 length
    orgEmail = StringField(required=True, unique=True)
    orgLink = StringField(required=True)
    orgStatus = StringField(required=True)

    meta = {
        'collection': 'organizations',
        'indexes': [
            'orgEmail',
            'orgName'
        ]
    }
