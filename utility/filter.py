from datetime import datetime, timedelta

class FilterDateTime:
    def __init__(self) -> None:
        pass

    def format_datetime(self, dt):
        return dt.strftime('%Y-%m-%d %H:%M:%S')

    def get_today(self):
        now = datetime.now().date()
        start_of_today = datetime.combine(now, datetime.min.time())
        end_of_today = start_of_today + timedelta(days=1) - timedelta(seconds=1)
        return {"gt": self.format_datetime(start_of_today), "lt": self.format_datetime(end_of_today)}

    def get_this_week(self):
        now = datetime.now()
        start_of_week = now - timedelta(days=now.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0)
        end_of_week = end_of_week.replace(hour=23, minute=59, second=59)
        return {"gt": self.format_datetime(start_of_week), "lt": self.format_datetime(end_of_week)}

    def get_this_month(self):
        now = datetime.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0)
        if now.month == 12:
            end_of_month = start_of_month.replace(year=now.year + 1, month=1) - timedelta(seconds=1)
        else:
            end_of_month = (start_of_month.replace(month=now.month + 1) - timedelta(seconds=1))
        return {"gt": self.format_datetime(start_of_month), "lt": self.format_datetime(end_of_month)}

    def get_this_year(self):
        now = datetime.now()
        start_of_year = now.replace(month=1, day=1, hour=0, minute=0, second=0)
        end_of_year = now.replace(month=12, day=31, hour=23, minute=59, second=59)
        return {"gt": self.format_datetime(start_of_year), "lt": self.format_datetime(end_of_year)}