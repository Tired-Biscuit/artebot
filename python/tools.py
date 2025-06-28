import subprocess
import python.db as db
import time

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