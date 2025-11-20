from mongoengine import Document, StringField, DateTimeField


class Shift(Document):
    shiftType = StringField(
        required=True,
        choices=["Day", "Night", "Rotational"]
    )
    fromTime = DateTimeField(required=True)
    endTime = DateTimeField(required=True)

    meta = {
        'collection': 'shifts',
        'indexes': [
            'shiftType',
            {
                'fields': ['fromTime', 'endTime'],
                'unique': True
            }
        ]
    }
