import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import calendar

LOCAL_TZ = ZoneInfo("Europe/Paris")
DAY_DURATION = 86400

def local_datetime_as_epoch(datetime_struct: datetime) -> int:
    """
    Takes a datetime struct with a local time and returns a timestamp as if the local time was utc time

    @flag struct_to_epoch
    @flag local_as_utc
    """
    return calendar.timegm(datetime_struct.timetuple())

def utc_datetime_to_local_datetime(utc_datetime: datetime) -> datetime:
    """
    Converts utc datetime to local datetime

    @flag utc_to_local
    """
    if utc_datetime.tzinfo is None:
        utc_datetime = utc_datetime.replace(tzinfo=ZoneInfo("UTC"))
    else:
        utc_datetime = utc_datetime.astimezone(ZoneInfo("UTC"))

    return utc_datetime.astimezone(LOCAL_TZ)

def local_datetime_as_utc_datetime(local_datetime: datetime) -> datetime:
    """
    Converts local datetime as utc datetime

    @flag local_as_utc
    """
    return local_datetime.replace(tzinfo=None)

def utc_struct_to_local_as_epoch(datetime_struct: datetime) -> int:
    """
    Takes a datetime struct with a utc time, converts it to local time, and returns a timestamp as if the local time was utc time

    @flag struct_to_epoch
    @flag utc_to_local_as_utc
    """
    if datetime_struct.tzinfo is None:
        custom_struct = datetime_struct.replace(tzinfo=ZoneInfo("UTC"))
    else:
        custom_struct = datetime_struct.astimezone(ZoneInfo("UTC"))

    custom_struct = custom_struct.astimezone(LOCAL_TZ)
    custom_struct = custom_struct.replace(tzinfo=None)
    return local_datetime_as_epoch(custom_struct)

def ics_to_datetime(ics_string: str) -> datetime:
    """
    Parse ics time string and returns a local datetime struct (no timezone operations)

    @flag ics
    @flag parser
    @flag struct
    @flag datetime_struct
    """
    return datetime.strptime(ics_string, "%Y%m%dT%H%M%SZ")

def gcal_to_datetime(google_calendar_string: str) -> datetime:
    """
    Parse google calendar time string and returns a local datetime struct

    @flag google_calendar
    @flag parser
    @flag struct
    @flag datetime_struct
    """
    print(google_calendar_string)
    return datetime.strptime(google_calendar_string.split("+")[0], "%Y-%m-%dT%H:%M:%S")

def datetime_to_gcal(date: str) -> str:
    """
    Parse datetime time string (YYYYMMDDHHMM[SS]) and returns corresponding it in an ISO8601 (RFC 3339) compliant format

    @flag google_calendar
    """
    if len(date) == 14:
        dt = datetime.strptime(date, "%Y%m%d%H%M%S")
    else:
        dt = datetime.strptime(date, "%Y%m%d%H%M")

    return dt.isoformat()

def epoch_to_gcal(epoch: str) -> str:
    """
    Converts an epoch time (seconds since 1970-01-01 UTC) to a Google Calendar ISO8601 string

    @flag google_calendar
    @flag epoch
    """
    dt = datetime.fromtimestamp(int(epoch))
    return dt.isoformat()

def add_duration_to_time(hhmm: str, duration: int) -> str:
    """"
    Add duration to a datetime time (HHMM)
    Duration in seconds

    @flag datetime
    @flag duration
    """
    dt = datetime.strptime(hhmm, "%H%M")
    dt += timedelta(seconds=duration)
    return dt.strftime("%H%M")

def yyyymmddhhmmss_to_datetime(time_string: str) -> datetime:
    """
    Parse string and return local datetime

    @flag YYYYMMDDHHMMSS
    @flag parser
    @flag struct
    @flag datetime_struct
    """
    return datetime.strptime(time_string, "%Y%m%d%H%M%S")

def ics_to_epoch(ics_time: str) -> int:
    """
    Returns epoch from ics string (interprets local time as utc time)

    @flag ics_to_epoch
    """
    return local_datetime_as_epoch(local_datetime_as_utc_datetime(utc_datetime_to_local_datetime(ics_to_datetime(ics_time))))

def gcal_to_epoch(gcal_time: str) -> int:
    """
    Returns epoch from gcal string (interprets local time as utc time)

    @flag gcal_to_epoch
    """
    if "Z" not in gcal_time:
        return local_datetime_as_epoch(gcal_to_datetime(gcal_time))
    else:
        print("Wrong calendar timezone")
        raise Exception("Wrong calendar timezone!")


def punctual_constraint_to_epoch(time_string: str) -> int:
    """
    Returns epoch from punctual constraint string (YYYYMMDDHHMMSS) (interprets local time as utc time)

    @flag punctual_constraint_to_epoch
    """
    return local_datetime_as_epoch(yyyymmddhhmmss_to_datetime(time_string))

def week_day_to_week_index(week_day: str):
    """
    Takes a french week day and returns its corresponding week index 1-7

    @flag week_day
    """
    days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

    if week_day == "Tous" or week_day == "tous" or week_day == "tous les jours" or week_day == "Tous les jours":
        day = 8
    else:
        try:
            day = days.index(str.capitalize(week_day)) + 1
        except ValueError:
            raise ValueError(f"Invalid week day: {week_day}. Must be one of {days}.")
    return day

def week_index_to_week_day(week_index: int):
    """
    Takes a week index 1-7 and returns the corresponding french week day

    @flag week_day
    """
    days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    return days[week_index-1] if 0< week_index and week_index <= 7 else "Tous les jours"

def get_nbdays(epoch_time: int) -> int:
    """
    Returns the number of days from 01/01/1970

    @flag epoch
    """
    return epoch_time//DAY_DURATION

def get_nbweeks(epoch_time: int) -> int:
    """
    Returns the number of weeks since 5th of Jan., 1970

    @flag epoch
    """
    # The +3*DAY_DURATION is because the 01/01/1970 is a thursday, we have to correct this bias in order to have a coherent result after the division
    return (epoch_time+3*DAY_DURATION)//(DAY_DURATION*7)

def get_first_day_of_week(nbweeks: int) -> int:
    """
    Returns the epoch date of the first day of the current week

    @flag epoch
    """
    return nbweeks*DAY_DURATION*7-3*DAY_DURATION

def is_week_index_before_today(week_index: int) -> bool:
    """
    Returns if week day number (1-7) is before today
    """
    return week_index < time.gmtime().tm_wday + 1

def is_day_before_today(day: int) -> bool:
    """
    Returns if a day is before today
    """
    return day//DAY_DURATION < time.time()//DAY_DURATION

def is_week_before_today(week: int) -> bool:
    """
    Returns if week is before today's week
    """
    return week < get_nbweeks(int(time.time()))