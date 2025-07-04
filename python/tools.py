import subprocess
import time
import os
import json
from datetime import timezone, timedelta, datetime

CEST = timezone(timedelta(hours=2), name="CEST")
CET  = timezone(timedelta(hours=1), name="CET")

DELTA_TIME = 14400
UPDATE_TIME = time.time()

def download_timetables():
    """
    Downloads timetables as .ics files in ./timetables
    
    returns: True if operation successful 
    """
    r = subprocess.call("./scripts/auto_update.sh")
    return r == 0

def add_calendar(calendar_id):
    """
    Adds calendar to data.json
    """
    if os.path.exists("data.json"):
        data = {}
        with open("data.json", "r") as f:
            data = json.loads(f.read())
        with open("data.json", "w") as f:
            if calendar_id not in data["calendar_ids"]:
                data["calendar_ids"].append(calendar_id)
                f.write(json.dumps(data))
    else:
        data = {"calendar_ids":[calendar_id]}
        with open("data.json", "w") as f:
                f.write(json.dumps(data))

def delete_calendar(calendar_id):
    """
    Removes calendar from data.json
    """
    if os.path.exists("data.json"):
        with open("data.json", "r") as f:
            data = json.loads(f.read())
        with open("data.json", "w") as f:
            if calendar_id in data["calendar_ids"]:
                data["calendar_ids"].remove(calendar_id)
                f.write(json.dumps(data))

def ics_to_unixepoch(ics_time: str) -> int:
    """
    Converts an ICS timestamp (GMT) with format YYYYMMDDTHHMMSSZ to a Unix epoch timestamp.
    """
    time_struct = datetime.strptime(ics_time, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    return int(time_struct.timestamp())

def cal_to_unixepoch(cal_time: str) -> int:
    """
    Converts a Google Calendar timestamp with format YYYY-MM-DDTHH:MM:SS+HH:MM (local+time zone difference) to a Unix epoch timestamp (UTC).
    """
    time_struct = time.strptime(cal_time[:-6], "%Y-%m-%dT%H:%M:%S")
    return int(time.mktime(time_struct))