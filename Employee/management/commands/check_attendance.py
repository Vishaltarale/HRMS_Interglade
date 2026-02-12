# Employee/management/commands/check_attendance.py
from django.core.management.base import BaseCommand
from Employee.attendance_checker import (
    mark_absent_for_date, 
    check_and_mark_all_absent,
    get_employees_to_check_now
)
from Employee.startup import create_missing_attendance_records
from utils.timezone_utils import get_current_date_ist
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Manually check and mark attendance as absent'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to check backwards (default: 7)'
        )
        parser.add_argument(
            '--today-only',
            action='store_true',
            help='Only check today'
        )
        parser.add_argument(
            '--create-records',
            action='store_true',
            help='Create missing attendance records first'
        )
        parser.add_argument(
            '--date',
            type=str,
            help='Check specific date (YYYY-MM-DD format)'
        )

    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS("🔍 ATTENDANCE CHECK STARTED"))
        self.stdout.write("="*70 + "\n")

        # Option 1: Create missing records first
        if options['create_records']:
            self.stdout.write("📋 Creating missing attendance records...")
            try:
                result = create_missing_attendance_records()
                
                if result.get('success'):
                    self.stdout.write(self.style.SUCCESS(
                        f"✅ Created {result.get('created')} records, "
                        f"Found {result.get('existing')} existing"
                    ))
                else:
                    self.stdout.write(self.style.ERROR(
                        f"❌ Error: {result.get('error')}"
                    ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Exception: {str(e)}"))
            
            self.stdout.write("")

        # Option 2: Check specific date
        if options.get('date'):
            try:
                # Validate date format
                check_date = datetime.strptime(options['date'], '%Y-%m-%d')
                check_date_str = check_date.strftime('%Y-%m-%d')
                
                self.stdout.write(f"🔍 Checking date: {check_date_str}")
                result = mark_absent_for_date(check_date_str)
                
                if result.get('success'):
                    self.stdout.write(self.style.SUCCESS(
                        f"✅ Marked {result.get('marked_absent')} as absent, "
                        f"Skipped {result.get('skipped')}, "
                        f"Skipped new {result.get('skipped_new', 0)}"
                    ))
                else:
                    self.stdout.write(self.style.ERROR(
                        f"❌ Error: {result.get('error')}"
                    ))
            except ValueError:
                self.stdout.write(self.style.ERROR(
                    "❌ Invalid date format. Use YYYY-MM-DD"
                ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Exception: {str(e)}"))
            
            self.stdout.write("\n" + "="*70)
            self.stdout.write(self.style.SUCCESS("✅ ATTENDANCE CHECK COMPLETED"))
            self.stdout.write("="*70 + "\n")
            return

        # Option 3: Check today only
        if options['today_only']:
            self.stdout.write("🔍 Checking today only...")
            
            try:
                current_date_str = get_current_date_ist()
                
                result = mark_absent_for_date(current_date_str)
                
                if result.get('success'):
                    self.stdout.write(self.style.SUCCESS(
                        f"✅ Marked {result.get('marked_absent')} as absent, "
                        f"Skipped {result.get('skipped')}, "
                        f"Skipped new {result.get('skipped_new', 0)}"
                    ))
                else:
                    self.stdout.write(self.style.ERROR(
                        f"❌ Error: {result.get('error')}"
                    ))
                
                # Show who should be marked now
                self.stdout.write("\n📋 Employees eligible for absent marking right now:")
                to_mark = get_employees_to_check_now()
                
                if to_mark:
                    for item in to_mark:
                        # Unpack tuple safely
                        if isinstance(item, tuple) and len(item) >= 3:
                            attendance, cutoff, reason = item[0], item[1], item[2]
                            employee = attendance.employee
                            shift = employee.shiftId if employee else None
                            
                            employee_name = f"{employee.firstName} {employee.lastName}" if employee else "Unknown"
                            shift_type = shift.shiftType if shift else 'N/A'
                            
                            self.stdout.write(
                                f"  - {employee_name} (Shift: {shift_type})"
                            )
                            self.stdout.write(f"    {reason}")
                        else:
                            self.stdout.write(f"  - Invalid data format: {item}")
                else:
                    self.stdout.write("  (None)")
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Exception: {str(e)}"))
                import traceback
                traceback.print_exc()
            
            self.stdout.write("\n" + "="*70)
            self.stdout.write(self.style.SUCCESS("✅ ATTENDANCE CHECK COMPLETED"))
            self.stdout.write("="*70 + "\n")
            return

        # Option 4: Comprehensive check (default)
        days = options.get('days', 7)
        self.stdout.write(f"🔍 Running comprehensive check for past {days} days...")
        
        try:
            result = check_and_mark_all_absent(days_back=days)
            
            if result.get('success'):
                self.stdout.write(self.style.SUCCESS(
                    f"\n✅ COMPREHENSIVE CHECK COMPLETE"
                ))
                self.stdout.write(f"Total marked absent: {result.get('total_marked')}")
                
                # Show daily breakdown
                self.stdout.write("\n📊 Daily Breakdown:")
                daily_results = result.get('daily_results', [])
                
                if daily_results:
                    for daily in daily_results:
                        if daily.get('success'):
                            self.stdout.write(
                                f"  {daily.get('date')}: "
                                f"{daily.get('marked_absent')} marked, "
                                f"{daily.get('skipped')} skipped (no shift), "
                                f"{daily.get('skipped_new', 0)} skipped (new records)"
                            )
                        else:
                            self.stdout.write(
                                f"  {daily.get('date')}: "
                                f"❌ Error: {daily.get('error', 'Unknown error')}"
                            )
                else:
                    self.stdout.write("  (No daily results)")
            else:
                self.stdout.write(self.style.ERROR(
                    f"❌ Error: {result.get('error')}"
                ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Exception: {str(e)}"))
            import traceback
            traceback.print_exc()

        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS("✅ ATTENDANCE CHECK COMPLETED"))
        self.stdout.write("="*70 + "\n")