# Employee/management/commands/test_attendance.py
from django.core.management.base import BaseCommand
from Employee.attendance_checker import (
    mark_absent_for_date, 
    check_and_mark_all_absent,
    get_employees_to_check_now,
    manual_mark_absent_immediately,
    get_shift_absent_cutoff_time
)
from Employee.models import Employee, Attendance
from Employee.startup import create_missing_attendance_records
from utils.timezone_utils import today, current_time
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Test and debug attendance absent marking logic'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-now',
            action='store_true',
            help='Show employees who should be marked absent right now'
        )
        parser.add_argument(
            '--mark-today',
            action='store_true',
            help='Mark absent for today (respects grace period)'
        )
        parser.add_argument(
            '--force-mark-today',
            action='store_true',
            help='FORCE mark absent for today (ignores grace period)'
        )
        parser.add_argument(
            '--comprehensive',
            type=int,
            default=0,
            help='Run comprehensive check for N days back'
        )
        parser.add_argument(
            '--create-records',
            action='store_true',
            help='Create missing attendance records first'
        )
        parser.add_argument(
            '--show-cutoffs',
            action='store_true',
            help='Show cutoff times for all shifts'
        )
        parser.add_argument(
            '--date',
            type=str,
            help='Check specific date (YYYY-MM-DD format)'
        )

    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*80)
        self.stdout.write(self.style.SUCCESS("🔍 ATTENDANCE TESTING AND DEBUGGING"))
        self.stdout.write("="*80 + "\n")

        # Show current time
        current_dt = today()
        current_tm = current_time()
        self.stdout.write(f"📅 Current Date: {current_dt}")
        self.stdout.write(f"⏰ Current Time: {current_tm}\n")

        # Option: Create missing records first
        if options['create_records']:
            self.stdout.write(self.style.WARNING("📋 Creating missing attendance records...\n"))
            result = create_missing_attendance_records()
            
            if result.get('success'):
                self.stdout.write(self.style.SUCCESS(
                    f"✅ Created {result.get('created')} records, "
                    f"Found {result.get('existing')} existing\n"
                ))
            else:
                self.stdout.write(self.style.ERROR(
                    f"❌ Error: {result.get('error')}\n"
                ))

        # Option: Show cutoff times for all shifts
        if options['show_cutoffs']:
            self.stdout.write(self.style.WARNING("⏰ SHIFT CUTOFF TIMES:\n"))
            from Shifts.models import Shift
            
            shifts = Shift.objects.all()
            for shift in shifts:
                cutoff = get_shift_absent_cutoff_time(shift)
                self.stdout.write(
                    f"  📌 {shift.shiftType}: "
                    f"Start: {shift.fromTime.time()}, "
                    f"End: {shift.endTime.time()}, "
                    f"Cutoff (End-2hrs): {cutoff}"
                )
            self.stdout.write("")

        # Option: Check who should be marked absent NOW
        if options['check_now']:
            self.stdout.write(self.style.WARNING("🔍 EMPLOYEES TO MARK ABSENT NOW:\n"))
            to_mark = get_employees_to_check_now()
            
            if to_mark:
                for attendance, cutoff, reason in to_mark:
                    employee = attendance.employee
                    shift = employee.shiftId
                    self.stdout.write(
                        f"  ❌ {employee.firstName} {employee.lastName}\n"
                        f"     Shift: {shift.shiftType} | {reason}\n"
                        f"     Record created: {attendance.created_at}"
                    )
                self.stdout.write(self.style.ERROR(f"\nTotal: {len(to_mark)} employees should be marked absent\n"))
            else:
                self.stdout.write(self.style.SUCCESS("  ✅ No employees to mark absent right now\n"))

        # Option: Mark absent for today (with grace period)
        if options['mark_today']:
            self.stdout.write(self.style.WARNING("⏰ Marking absent for TODAY (with grace period)...\n"))
            result = mark_absent_for_date(current_dt, skip_new_records=True)
            
            if result.get('success'):
                self.stdout.write(self.style.SUCCESS(
                    f"✅ Marked: {result.get('marked_absent')}\n"
                    f"   Skipped (no shift): {result.get('skipped')}\n"
                    f"   Skipped (new records): {result.get('skipped_new', 0)}\n"
                ))
            else:
                self.stdout.write(self.style.ERROR(f"❌ Error: {result.get('error')}\n"))

        # Option: FORCE mark absent for today (ignore grace period)
        if options['force_mark_today']:
            self.stdout.write(self.style.ERROR("🔨 FORCE marking absent for TODAY (ignoring grace period)...\n"))
            result = manual_mark_absent_immediately(current_dt)
            
            if result.get('success'):
                self.stdout.write(self.style.SUCCESS(
                    f"✅ Force marked: {result.get('marked_absent')}\n"
                    f"   Skipped (no shift): {result.get('skipped')}\n"
                ))
            else:
                self.stdout.write(self.style.ERROR(f"❌ Error: {result.get('error')}\n"))

        # Option: Check specific date
        if options['date']:
            try:
                check_date = datetime.strptime(options['date'], '%Y-%m-%d').date()
                
                self.stdout.write(self.style.WARNING(f"📅 Checking date: {check_date}\n"))
                
                # Past dates don't skip new records
                skip_new = (check_date == current_dt)
                result = mark_absent_for_date(check_date, skip_new_records=skip_new)
                
                if result.get('success'):
                    self.stdout.write(self.style.SUCCESS(
                        f"✅ Marked: {result.get('marked_absent')}\n"
                        f"   Skipped: {result.get('skipped')}\n"
                    ))
                else:
                    self.stdout.write(self.style.ERROR(f"❌ Error: {result.get('error')}\n"))
            except ValueError:
                self.stdout.write(self.style.ERROR("❌ Invalid date format. Use YYYY-MM-DD\n"))

        # Option: Comprehensive check
        if options['comprehensive'] > 0:
            days = options['comprehensive']
            self.stdout.write(self.style.WARNING(f"🔍 Running comprehensive check for {days} days...\n"))
            
            result = check_and_mark_all_absent(days_back=days)
            
            if result.get('success'):
                self.stdout.write(self.style.SUCCESS(f"✅ COMPREHENSIVE CHECK COMPLETE\n"))
                self.stdout.write(f"Total marked absent: {result.get('total_marked')}\n")
                
                # Show daily breakdown
                self.stdout.write("\n📊 Daily Breakdown:")
                for daily in result.get('daily_results', []):
                    if daily.get('success'):
                        self.stdout.write(
                            f"  {daily.get('date')}: "
                            f"{daily.get('marked_absent')} marked, "
                            f"{daily.get('skipped')} skipped"
                        )
            else:
                self.stdout.write(self.style.ERROR(f"❌ Error: {result.get('error')}\n"))

        # Show summary of pending attendance
        self.stdout.write("\n" + "-"*80)
        self.stdout.write("📊 CURRENT STATUS SUMMARY:\n")
        
        today_pending = Attendance.objects.filter(date=current_dt, status='pending').count()
        today_absent = Attendance.objects.filter(date=current_dt, status='absent').count()
        today_present = Attendance.objects.filter(date=current_dt, status='present').count()
        
        self.stdout.write(f"  Today's Attendance ({current_dt}):")
        self.stdout.write(f"    ⏳ Pending: {today_pending}")
        self.stdout.write(f"    ✅ Present: {today_present}")
        self.stdout.write(f"    ❌ Absent: {today_absent}")
        
        self.stdout.write("\n" + "="*80)
        self.stdout.write(self.style.SUCCESS("✅ TEST COMPLETED"))
        self.stdout.write("="*80 + "\n")


# USAGE EXAMPLES:
# ================
#
# 1. See who should be marked absent RIGHT NOW:
#    python manage.py test_attendance --check-now
#
# 2. Show all shift cutoff times:
#    python manage.py test_attendance --show-cutoffs
#
# 3. Create missing records then check who to mark:
#    python manage.py test_attendance --create-records --check-now
#
# 4. Mark absent for today (respects 30-min grace period):
#    python manage.py test_attendance --mark-today
#
# 5. FORCE mark absent (ignores grace period):
#    python manage.py test_attendance --force-mark-today
#
# 6. Check specific date:
#    python manage.py test_attendance --date 2024-12-20
#
# 7. Comprehensive check for past 7 days:
#    python manage.py test_attendance --comprehensive 7
#
# 8. Full diagnostic (recommended):
#    python manage.py test_attendance --show-cutoffs --check-now