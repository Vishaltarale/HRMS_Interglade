# Employee/apps.py
from django.apps import AppConfig
import sys
import os 


class EmployeeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Employee'
    
    def ready(self):
        """
        This method runs when Django starts
        We use it to:
        1. Create missing attendance records
        2. Check and mark absent for past days (in case server was down)
        3. Start the scheduler
        """
        # Only run during actual server start (not during migrations, shell, etc.)
        run_commands = ['runserver', 'gunicorn', 'daphne', 'uwsgi']
        should_run = any(cmd in ' '.join(sys.argv) for cmd in run_commands)
        
        # Also check if running via WSGI
        if not should_run:
            should_run = 'wsgi' in sys.argv[0].lower()
        
        # Avoid running in Django migrations or management commands
        if 'migrate' in sys.argv or 'makemigrations' in sys.argv:
            should_run = False
        
        if should_run:
            print("\n" + "="*70)
            print("🚀 DJANGO SERVER STARTING - INITIALIZING ATTENDANCE SYSTEM")
            print("="*70)
            
            # Import here to avoid circular imports
            from Employee.startup import run_startup_tasks
            from Employee.scheduler import start_scheduler
            
            # Small delay to ensure MongoDB connections are ready
            import time
            time.sleep(2)
            
            try:
                # Run all startup tasks
                result = run_startup_tasks()
                
                if result.get('success'):
                    print("\n✅ STARTUP TASKS COMPLETED SUCCESSFULLY")
                    
                    # Show summary
                    att_result = result.get('attendance_result', {})
                    abs_result = result.get('absent_result', {})
                    
                    print(f"📋 Attendance Records: {att_result.get('created', 0)} created, {att_result.get('existing', 0)} existing")
                    print(f"📊 Absent Marking: {abs_result.get('total_marked', 0)} employees marked absent")
                else:
                    print(f"\n⚠️ SOME TASKS FAILED: {result.get('error')}")
                
                # Start the scheduler
                print("\n🔧 Starting attendance scheduler...")
                start_scheduler()
                print("✅ Scheduler started successfully")
                
            except Exception as e:
                print(f"\n❌ ERROR during initialization: {str(e)}")
                import traceback
                traceback.print_exc()
            
            print("="*70 + "\n")