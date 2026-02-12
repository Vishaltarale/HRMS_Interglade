# Employee/management/commands/create_attendance.py
from django.core.management.base import BaseCommand
from Employee.startup import create_missing_attendance_records
from utils.timezone_utils import get_current_date_ist


class Command(BaseCommand):
    help = 'Manually create missing attendance records for today (MongoEngine)'
    
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('📋 CREATING ATTENDANCE RECORDS'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
        
        # Get current date
        current_date = get_current_date_ist()
        self.stdout.write(f"📅 Date: {current_date}\n")
        
        # Run the creation function
        result = create_missing_attendance_records()
        
        if result.get('success'):
            self.stdout.write(self.style.SUCCESS(
                f"\n✅ SUCCESS"
            ))
            self.stdout.write(f"Created: {result.get('created')} records")
            self.stdout.write(f"Existing: {result.get('existing')} records")
            self.stdout.write(f"Total Employees: {result.get('total_employees')}")
            self.stdout.write(f"Date: {result.get('date')}")
        else:
            self.stdout.write(self.style.ERROR(
                f"\n❌ FAILED: {result.get('error')}"
            ))
        
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('✅ COMMAND COMPLETED'))
        self.stdout.write('='*70 + '\n')