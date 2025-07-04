import subprocess
import python.db as db
import time
import os
import json
import python.googleutils as googleutils

DELTA_TIME = 14400
UPDATE_TIME = time.time()

def download_timetables():
    """
    Downloads timetables as .ics files in ./timetables
    
    returns: True if operation successful 
    """
    r = subprocess.call("./scripts/auto_update.sh")
    return r == 0

def update_timetables():
    """
    Downloads timetables and updates the database
    """
    if download_timetables():
        db.update_timetables()

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

def update_calendars():
    """
    Downloads Google Calendars in data.json and updates the database
    """
    if not os.path.exists("./data.json"):
        print("No calendars added.")
        return False

    with open("./data.json") as f:
        calendar_ids = json.loads(f.read())["calendar_ids"]
        if len(calendar_ids) == 0:
            print("Empty calendar list")
            return False
    i=0
    for calendar_id in calendar_ids:
        i+=1
        result = googleutils.download_calendar(calendar_id)
        if result[0] and len(result[1]) > 0:
            print(f"Calendar update ({i}/{len(calendar_ids)}): {'Success' if (val := db.update_calendar(result[1])) in [[], None] else val}")
