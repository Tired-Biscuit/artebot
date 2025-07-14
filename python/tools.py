import subprocess
import time
import os
import json
from datetime import timezone, timedelta, datetime
import re

import discord.embeds

CEST = timezone(timedelta(hours=2), name="CEST")
CET  = timezone(timedelta(hours=1), name="CET")

DELTA_TIME = 14400
UPDATE_TIME = time.time()
DAY_DURATION = 86400

def create_data_file():
    if not os.path.exists("data.json"):
        data = {"calendar_ids":[], "setlists":[], "admins":[], "owners":[]}
        with open("data.json", "w") as f:
            f.write(json.dumps(data))
    else:
        data = None
        with open("data.json", "r") as f:
            data = f.read()
        if data == "":
            data = {"calendar_ids": [], "setlists": [], "admins": [], "owners": []}
            with open("data.json", "w") as f:
                f.write(json.dumps(data))

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
    create_data_file()
    data = {}
    with open("data.json", "r") as f:
        data = json.loads(f.read())
    if data != {}:
        with open("data.json", "w") as f:
            if calendar_id not in data["calendar_ids"]:
                data["calendar_ids"].append(calendar_id)
                f.write(json.dumps(data))

def remove_calendar(calendar_id):
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

def local_to_unixepoch(local_time: str) -> int:
    """
    Converts a local time given in YYYYMMDDHHMMSS format to epoch
    """
    time_struct = time.strptime(local_time, "%Y%m%d%H%M%S")
    return int(time.mktime(time_struct))

def cal_to_unixepoch(cal_time: str) -> int:
    """
    Converts a Google Calendar timestamp with format YYYY-MM-DDTHH:MM:SS+HH:MM (local+time zone difference) to a Unix epoch timestamp (UTC).
    """
    time_struct = time.strptime(cal_time[:-6], "%Y-%m-%dT%H:%M:%S")
    return int(time.mktime(time_struct))

def week_day_to_week_index(week_day: str):
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
    days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    return days[week_index-1] if 0< week_index and week_index <= 7 else "Tous les jours"

def parse_date(date: str) -> str:
    """
    Parses a date string and returns it in the YYYYMMDD format.
    """
    now = datetime.now()

    match = re.match(
        r"^(\d{1,2})[\/\-\s]([A-Za-zéa-zA-Z]{3,}\.?|\d{1,2})(?:[\/\-\s](\d{2,4}))?$", date
    )

    month_map = {
        "janvier": "01", "jan": "01", "january": "01",
        "février": "02", "fevrier": "02", "fév": "02", "fev": "02", "february": "02", "feb": "02",
        "mars": "03", "mar": "03", "march": "03",
        "avril": "04", "avr": "04", "april": "04", "apr": "04",
        "mai": "05", "may": "05",
        "juin": "06", "jun": "06", "june": "06",
        "juillet": "07", "juil": "07", "july": "07", "jul": "07",
        "août": "08", "aout": "08", "august": "08", "aug": "08",
        "septembre": "09", "sep": "09", "sept": "09", "september": "09",
        "octobre": "10", "oct": "10", "october": "10",
        "novembre": "11", "nov": "11", "november": "11",
        "décembre": "12", "decembre": "12", "déc": "12", "dec": "12", "december": "12"
    }

    if match:
        day, month, year = match.groups()
        if len(day) == 1:
            day = "0" + day
        if len(month) == 1:
            month = "0" + month

        if len(month) > 2:
            try:
                if month[-1] == ".":
                    month = month[:-1]
                month = month_map[month]
            except:
                raise ValueError("Date could not be parsed.")

        if year is None:
            year = str(now.year)

            parsed_date = int(month + day)

            today = int(now.strftime("%m%d"))
            if parsed_date < today:
                year = str(now.year + 1)

        elif len(year) == 2:
            year = "20" + year
        
        if len(year) == 4 and 1 <= int(day) <= 31 and 1 <= int(month) <= 12:
            return year + month + day


    
    date = date.capitalize()
    if date in ["Aujourd'hui", "Aujourdhui", "Aujourd’hui", "Today"]:
        return now.strftime("%Y%m%d")
    
    if date in ["Demain", "Tomorrow"]:
        return (now + timedelta(days=1)).strftime("%Y%m%d")

    if date in ["Après-demain", "Après demain", "Apres-demain", "Apres demain", "Overmorrow"]:
        return (now + timedelta(days=2)).strftime("%Y%m%d")
    

    raise ValueError("Date could not be parsed.")


def parse_time(time_string: str) -> str:
    """
    Parses a time string and returns it in the HHMM format.
    """
    match = re.match(
        r"^(\d{1,2})\s*[-:h]?\s*(\d{1,2})?", time_string
    )

    if match:
        h, m = match.groups()

        if len(h) == 1:
            h = "0" + h
        
        if m is None:
            m = "00"
        
        if len(m) == 1:
            m = "0" + m

        if int(h) <= 23 and int(m) <= 59:
            return h + m
    
    time_string = time_string.capitalize()

    if time_string in ["Midi", "Noon"]:
        return "1200"

    raise ValueError("Time could not be parsed.")

def parse_duration(duration: str) -> int:
    """
    Parses a duration string (precision up to minutes) and returns the corresponding duration in seconds.
    """
    match = re.match(
        r"^(\d{1,3})\s*m", duration
    )

    if match:
        m = match.groups()[0]
        return 60*int(m)


    match = re.match(
        r"^(\d{1,2})\s*[-:h]?\s*(\d{1,2})?", duration
    )

    if match:
        h, m = match.groups()
        return 3600*int(h) + 60*int(m) if m is not None else 3600*int(h)

def parse_mail(mail: str) -> str:
    """
    Returns the name of the owner of the mail address ([first_name].[last_name]@[...] format) 
    """
    mail = mail.split("@")[0].split(".")
    
    if len(mail) != 2:
        raise ValueError("Format de l'adresse mail incorrecte...")

    return mail[0].capitalize() + " " + mail[1].upper()



def date_to_string(date: str) -> str:
    """
    Returns a readable string in french of the date given in argument.

    Args:
        date (str): The date, in YYYYMMDD format
    """
    today = int(datetime.now().strftime("%Y%m%d"))

    if str(today) == date:
        return "**aujourd'hui**"

    if str(today + 1) == date:
        return "**demain**"

    if str(today + 2) == date:
        return "**après-demain**"

    return f"le **{date[-2:]}/{date[4:6]}/{date[:4]}**"

def formatted_time_span_string(start: str, end: str) -> str:
    """
    Returns a readable string in french of the time span given in argument.

    Args:
        start (str): The start time of the span, in HHMM format
        end (str): The end time of the span, in HHMM format
    """
    res = ""
    
    if start == "0000" and end == "2359":
        return "**toute la journée**"

    if start == "0000":
        res += "jusqu'"
    else:
        if start[0] == '0':
            start = start[1:]

        if start[-2:] == "00":
           res += f"de **{start[:-2]} h** "
        else:
           res += f"de **{start[:-2]} h {start[-2:]}** "
    
    if end == "2359":
        return "à partir " + res[:-1]

    else:
        if end[0] == '0':
            end = end[1:]

        if end[-2:] == "00":
           res += f"à **{end[:-2]} h**"
        else:
           res += f"à **{end[:-2]} h {end[-2:]}**" 
    
    return res

def time_span_to_string(start_time: int, end_time: int) -> str:
    """"
    Returns a Markdown-formatted string for a time span (epoch values)
    """
    return formatted_time_span_string(time.strftime("%H%M", time.gmtime(start_time)), time.strftime("%H%M", time.gmtime(end_time)))

def formatted_hhmm(time_string: str) -> str:
    """
    Returns a readable string in french of the time given in argument.

    Args:
        time (str): The time, in HHMM format
    """
    if time_string == "1200":
        return "midi"

    if time_string[0] == '0':
        time_string = time_string[1:]

    if time_string[-2:] == "00":
        return f"{time_string[:-2]} h"
    else:
        return f"{time_string[:-2]} h {time_string[-2:]}"
        
def duration_to_string(duration: int) -> str:
    """
    Returns a readable string in french of the duration given in argument.

    Args:
        duration (int): The duration in seconds
    """
    res = ""
    if duration >= 3600:
        res += f"{int(duration/3600)} h"


    if duration%3600 != 0:
        if res:
            res += " "
        res += f"{int(duration%3600 / 60)} m"
    
    return res

def epoch_to_short_date(epoch_time: int) -> str:
    """
    Returns the date in DD/MM format, accounting for recurring events (with epoch < 86400)
    """
    return time.strftime("%d/%m", time.gmtime(epoch_time))

def get_constraint_description(constraint: list[int]) -> str:
    """
    Returns a formatted text for the corresponding constraint
    """
    return f"""Indisponible {time_span_to_string(constraint[0], constraint[1])}\n"""

def add_missing_recurring_constraints(message: str, constraints: list[list[int]], recurring_constraints: list[list[list[int]]], start_time: int, daynb: int, boundary: int) -> str:
    """
    Self-explanatory
    """
    j = 0
    # Iterate through recurring constraints until boundary
    while get_first_day_of_week(get_nbweeks(start_time)) + j * DAY_DURATION < boundary:
        if len(recurring_constraints[j]) > 0:
            # Write the day's date in case of a change of day number (which has to be updated after the call of the function (choose the boundary wisely))
            if get_nbdays(get_first_day_of_week(get_nbweeks(start_time)) + j * DAY_DURATION) != daynb: # TODO beware of the missing daynb update !
                message += "**" + "\n" + get_date_string(get_first_day_of_week(get_nbweeks(start_time)) + j * DAY_DURATION) + "**"

            # Pop the recurring constraints
            while len(recurring_constraints[j]) > 0: #TODO no check for boundary might cause errors ?
                message += "🟦 " + get_constraint_description(recurring_constraints[j].pop(0))
        j += 1
    return message

def get_constraints_week_description(constraints: list[list[int]], start_time: int) -> str:
    """
    Writes a message describing all musicians' constraints for the week of a given start time

    constraints: result of a db request as list of (start_time, end_time, week_day) from musician constraints sorted by start time
    start_time: epoch value of a day in the week
    """

    # Gets the week number to track for week change between constraints
    weeknb = get_nbweeks(start_time)
    i = 0
    # List of all recurring contraints for the week, per day (recurrent ones are put directly in each day)
    recurring_constraints = [[],[],[],[],[],[],[]]

    # First, start from the first constraint and continue until getting the first constraint from the right week
    while i < len(constraints) and get_nbweeks(constraints[i][0]) < weeknb:
        # At the beginning are all the recurring constraints
        if constraints[i][0] < DAY_DURATION and constraints[i][2] > 0:
            # They are added to their corresponding day
            if constraints[i][2] < 8:
                recurring_constraints[constraints[i][2]-1].append(constraints[i])
            else:
                # Daily constraint
                for day in recurring_constraints:
                    day.append(constraints[i])
        i+=1

    # From there, i is at the first constraint from start_day

    daynb = 0
    message = ""
    # Iterating through all constraints of the week
    while i < len(constraints) and get_nbweeks(constraints[i][0]) < weeknb+1:
        # First, write the date
        # daynb == 0 means the message is empty (could also check for message == "")
        # The second test is for when the next constraint happens on another day
        if daynb == 0 or get_nbdays(constraints[i][0]) > daynb:

            # Get recurring constraints happening after the last constraint and still int the previous day
            message = add_missing_recurring_constraints(message, constraints, recurring_constraints, start_time, daynb, (constraints[i][0] // DAY_DURATION) * DAY_DURATION)
            # Update the day tracker
            daynb = get_nbdays(constraints[i][0])
            # Add the date of the day in the message
            message += "**" + "\n" + get_date_string(constraints[i][0]) + "**"

        # Now check for recurring constraint happening before the constraint
        if len(recurring_constraints[time.gmtime(constraints[i][0]).tm_wday]) > 0: # First check the day
            # Then check wether or not to write the recurring constraints
            j = len(recurring_constraints[time.gmtime(constraints[i][0]).tm_wday][0])
            while j > 0:
                if recurring_constraints[time.gmtime(constraints[i][0]).tm_wday][0][0] < constraints[i][0]%DAY_DURATION:
                    message += "🟦 " + get_constraint_description(recurring_constraints[time.gmtime(constraints[i][0]).tm_wday].pop(0))
                    j = len(recurring_constraints[time.gmtime(constraints[i][0]).tm_wday][0])
                else:
                    j = 0

        # Finally, write the constraint
        message += "🟨 " + get_constraint_description(constraints[i])
        i+=1

    # In case of recurring constraints still happening after the last checked constraint, add them
    message = add_missing_recurring_constraints(message, constraints, recurring_constraints, start_time, daynb, get_first_day_of_week(weeknb + 1))
    return message

def get_date_string(epoch_time: int) -> str:
    """
    Returns a string formatted as this: Thursday 24/10 \n
    """
    return f"""{week_index_to_week_day(time.gmtime(epoch_time).tm_wday + 1)} {epoch_to_short_date(epoch_time)}\n"""

def get_nbdays(epoch_time: int) -> int:
    """
    Returns the number of days from 01/01/1970
    """
    return epoch_time//DAY_DURATION

def get_nbweeks(epoch_time: int) -> int:
    """
    Returns the number of weeks since 5th of Jan., 1970
    """
    # The +3*DAY_DURATION is because the 01/01/1970 is a thursday, we have to correct this bias in order to have a coherent result after the division
    return (epoch_time+3*DAY_DURATION)//(DAY_DURATION*7)

def get_first_day_of_week(nbweeks: int):
    return nbweeks*DAY_DURATION*7-3*DAY_DURATION

def get_constraint_message(constraints: list[list[int]], start_time) -> discord.embeds.Embed:
    message = discord.Embed(
        title=f"Semaine du {epoch_to_short_date(start_time)} au {epoch_to_short_date(get_first_day_of_week(get_nbweeks(start_time))+6*DAY_DURATION)}",
        description=get_constraints_week_description(constraints, start_time)
    )
    return message

def get_admins() -> list[int]:
    if os.path.exists("data.json"):
        with open("data.json", "r") as f:
            admins = json.loads(f.read())["admins"]
            return admins
    else:
        return []

def get_owners() -> list[int]:
    if os.path.exists("data.json"):
        with open("data.json", "r") as f:
            owners = json.loads(f.read())["owners"]
            return owners
    else:
        return []

def add_admin(uuid: int):
    create_data_file()
    data = None
    with open("data.json", "r") as f:
        data = json.loads(f.read())
    if data != None:
        with open("data.json", "w") as f:
            if uuid not in data["admins"]:
                data["admins"].append(uuid)
                f.write(json.dumps(data))

def remove_admin(uuid: int):
    if os.path.exists("data.json"):
        with open("data.json", "r") as f:
            data = json.loads(f.read())
        if data != None:
            with open("data.json", "w") as f:
                if uuid in data["admins"]:
                    data["admins"].remove(uuid)
                    f.write(json.dumps(data))

def add_setlist(setlist_link: str):
    create_data_file()
    data = None
    with open("data.json", "r") as f:
        data = json.loads(f.read())
    if data != None:
        with open("data.json", "w") as f:
            if setlist_link not in data["setlists"]:
                data["setlists"].append(setlist_link)
                f.write(json.dumps(data))

def get_setlists_links() -> list[str] | None:
    if os.path.exists("data.json"):
        with open("data.json", "r") as f:
            data = json.loads(f.read())
            return data["setlists"]

def get_setlists_names() -> list[str] | None:
    return None

def remove_setlist(index: int):
    if os.path.exists("data.json"):
        with open("data.json", "r") as f:
            data = json.loads(f.read())
        if data != None:
            with open("data.json", "w") as f:
                data["setlists"].delete(index)
                f.write(json.dumps(data))
