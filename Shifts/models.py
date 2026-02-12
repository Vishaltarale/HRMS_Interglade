from mongoengine import Document, StringField
from datetime import datetime, time


class Shift(Document):
    """
    Shift model with string-based time storage in IST
    
    Time format: "HH:MM:SS" in 24-hour IST (e.g., "09:00:00", "18:00:00")
    """
    shiftType = StringField(
        required=True, 
        choices=["Day", "Night", "Rotational", "Afternoon"]
    )
    
    # Times stored as strings in "HH:MM:SS" format (IST timezone)
    fromTime = StringField(required=True)  # e.g., "09:00:00"
    endTime = StringField(required=True)   # e.g., "18:00:00"
    lateMarkTime = StringField()          # e.g., "10:30:00"
    
    def clean(self):
        """Set lateMarkTime based on shift type if not provided."""
        if not self.lateMarkTime and self.fromTime:
            late_time_obj = None
            if self.shiftType == "Day":
                late_time_obj = time(10, 30, 0)
            elif self.shiftType == "Night":
                late_time_obj = time(22, 30, 0)  # 10:30 PM
            elif self.shiftType == "Afternoon":
                late_time_obj = time(15, 30, 0)  # 3:30 PM
            elif self.shiftType == "Rotational":
                # Extract hour from fromTime string
                try:
                    from_hour = int(self.fromTime.split(':')[0])
                    new_hour = (from_hour + 2) % 24
                    late_time_obj = time(new_hour, 30, 0)
                except:
                    late_time_obj = time(10, 30, 0)
            
            if late_time_obj:
                self.lateMarkTime = late_time_obj.strftime("%H:%M:%S")
    
    def get_from_time_obj(self):
        """Convert fromTime string to time object for comparisons"""
        try:
            return datetime.strptime(self.fromTime, "%H:%M:%S").time()
        except:
            return None
    
    def get_end_time_obj(self):
        """Convert endTime string to time object for comparisons"""
        try:
            return datetime.strptime(self.endTime, "%H:%M:%S").time()
        except:
            return None
    
    def get_late_mark_time_obj(self):
        """Convert lateMarkTime string to time object for comparisons"""
        try:
            return datetime.strptime(self.lateMarkTime, "%H:%M:%S").time()
        except:
            return None
    
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