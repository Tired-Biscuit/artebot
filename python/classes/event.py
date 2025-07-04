import time

class Event:
    """
    Represents a single event with a start and end time in Unix Epoch (UTC) format.
    """
    def __init__(self, start_time: int, end_time: int):
        self.start_time = start_time
        self.end_time = end_time
    
    def __str__(self):
        start = time.strftime("%d-%m-%Y %H:%M", time.localtime(self.start_time))
        end = time.strftime("%d-%m-%Y %H:%M", time.localtime(self.end_time))
        return f"Event between {start} and {end}"

def constraints_to_events(constraints: list[tuple]) -> list[Event]:
    """
    Converts a list of constraints provided by the database to a list of Event objects.
    
    Args:
        constraints (list): A list of tuples containing constraint data.
        
    Returns:
        list: A list of Event objects.
    """
    events = []

    for constraint in constraints:
        start_time = time.strptime(f"{constraint[1]} {constraint[2]}", "%d-%m-%Y %H:%M")
        end_time = time.strptime(f"{constraint[1]} {constraint[3]}", "%d-%m-%Y %H:%M")

        events.append(Event(int(time.mktime(start_time)), int(time.mktime(end_time))))
    return events

def school_events_to_events(constraints):
    """
    Converts a list of school events provided by the database to a list of Event objects.
    
    Args:
        constraints (list): A list of tuples containing school event data.
        
    Returns:
        list: A list of Event objects.
    """
    events = []

    for constraint in constraints:
        start_time = constraint[2]
        end_time = constraint[3]

        events.append(Event(start_time, end_time))

    return events

def google_events_to_events(constraints):
    """
    Converts a list of Google events provided by the database to a list of Event objects.
    
    Args:
        constraints (list): A list of tuples containing Google event data.
        
    Returns:
        list: A list of Event objects.
    """
    events = []

    for constraint in constraints:
        start_time = constraint[3]
        end_time = constraint[4]

        events.append(Event(start_time, end_time))

    return events

class RecurringEvent(Event):
    """
    Represents a recurring event happening weekly or daily.
    """

    def __init__(self, start_time: str, end_time: str, week_day: int):
        self.start_time = start_time # "HH:MM" format
        self.end_time = end_time # "HH:MM" format
        self.week_day = week_day # 1-7 for Monday to Sunday, 8 for every day

    def getEvents(self):
        pass

    def __str__(self):
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day = days[self.week_day - 1] if self.week_day <= 7 else "day"
        return f"Recurring event every {day} from {self.start_time} to {self.end_time}"
    
def recurring_constraints_to_events(constraints: list[tuple]) -> list[RecurringEvent]:
    """
    Converts a list of recurring constraints provided by the database to a list of RecurringEvent objects.
    
    Args:
        constraints (list): A list of tuples containing recurring constraint data.
        
    Returns:
        list: A list of RecurringEvent objects.
    """
    events = []

    for constraint in constraints:
        start_time = constraint[2]
        end_time = constraint[3]

        week_day = constraint[4]

        events.append(RecurringEvent(start_time, end_time, week_day))

    return events