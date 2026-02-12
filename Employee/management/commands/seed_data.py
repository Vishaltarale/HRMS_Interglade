from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from datetime import date

from Employee.models import Employee
from Orgnization.models import Organization
from Departments.models import Departments
from Shifts.models import Shift
from Employee.models import Address  # embedded doc

class Command(BaseCommand):
    help = "Seed Admin Employee (MongoEngine)"

    def handle(self, *args, **kwargs):

        admin_email = "admin@gmail.com"

        if Employee.objects(email=admin_email).first():
            self.stdout.write("Admin already exists")
            return

        # Required references (must exist)
        org = Organization.objects.first()
        dept = Departments.objects.first()
        shift = Shift.objects.first()

        if not org or not dept or not shift:
            self.stdout.write(
                self.style.ERROR("Organization, Department, and Shift must exist before seeding admin")
            )
            return

        address = Address(
            street="HQ Office",
            city="Pune",
            state="MH",
            zip="41,1001",
            country="India"
        )

        Employee.objects.create(
            firstName="Admin",
            middleName="",
            lastName="User",
            email=admin_email,
            password="admin123",
            mobileNumber="9999999999",
            gender="male",
            dob=date(1990, 1, 1),
            doj=date.today(),
            status="active",
            role="admin",

            organizationId=org,
            departmentId=dept,
            designationId="System Administrator",
            shiftId=shift,

            currentAddress=address,
            permanentAddress=address
        )

        self.stdout.write(self.style.SUCCESS("Admin employee created successfully"))
