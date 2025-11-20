from mongoengine import Document, StringField, IntField, EmailField

class Student(Document):
    name = StringField(required=True, max_length=100)
    age = IntField(required=True)
    email = EmailField(required=True, unique=True)
    course = StringField(required=True, max_length=100)

    meta = {'collection': 'students'}


class Employee(Document):
    pass