import subprocess
import time
import os
import json
from datetime import timezone, timedelta, datetime
import re

import python.timeutils as timeutils

EVENT_TYPES = {"School": 1, "Google": 2, "Constraint": 3}

CEST = timezone(timedelta(hours=2), name="CEST")
CET  = timezone(timedelta(hours=1), name="CET")

DELTA_TIME = 14400
UPDATE_TIME = time.time()

#########################################
#      data.json related operations     #
#########################################

def create_data_file():
    """
    Creates the data file and initialize all the necessary fields
    """
    val = {"calendar_ids": [],
        "setlists": [],
        "admins": [],
        "owners": [],
        "embed_colour": 10070709,
        "ignored_columns": ["Genre", "Statistiques"],
        "instruments": {"drums": ["Batterie"], "keys": ["Clavier"], "guitar": ["Guitare"], "bass": ["Basse"], "violin": ["Violon"], "voice": ["Voix", "Chant"], "cello": ["Violoncelle"], "contrabass": ["Contrebasse"], "accordion": ["Accord\u00e9on"], "flute": ["Fl\u00fbte"], "saxophone": ["Saxophone"], "brass": ["Cuivre"], "notes": ["Remarques"], "supervisor": ["Responsable"], "title": ["Titre"], "artist": ["Artiste"], "length": ["Dur\u00e9e"], "setlist_id": ["''"]},
        "groups": {
            "1A G1": "fise_1a_g1",
            "1A G2": "fise_1a_g2",
            "1A G3": "fise_1a_g3",
            "1A G4": "fise_1a_g4",
            "2A G1": "fise_2a_g1",
            "2A G2": "fise_2a_g2",
            "2A G3": "fise_2a_g3",
            "2A G4": "fise_2a_g4",
            "2A G5": "fise_2a_g5",
            "2A IAMD": "fise_2a_iamd",
            "2A IL": "fise_2a_il",
            "2A LE": "fise_2a_le",
            "2A SIE": "fise_2a_sie",
            "2A ISS": "fise_2a_iss",
            "3A IAMD": "fise_3a_iamd",
            "3A IL": "fise_3a_il",
            "3A LE": "fise_3a_le",
            "3A SIE": "fise_3a_sie",
            "3A ISS": "fise_3a_iss",
            "FISA 1A": "fisa_1a",
            "FISA 2A": "fisa_2a",
            "FISA 3A": "fisa_3a"
        }
    }
    if not os.path.exists("data.json"):
        # data = {"calendar_ids":[], "setlists":[], "admins":[], "owners":[], "embed_colour":10070709}
        with open("data.json", "w") as f:
            f.write(json.dumps(val))
    else:
        data = None
        with open("data.json", "r") as f:
            data = f.read()
        if data == "":
            data = val#{"calendar_ids": [], "setlists": [], "admins": [], "owners": [], "embed_colour":10070709}
            with open("data.json", "w") as f:
                f.write(json.dumps(data))

def get_groups() -> dict:
    """
    Returns a dictionnary with all groups and their underscored values

    @flag data
    """
    create_data_file()
    with open("data.json", "r") as f:
        groups = json.loads(f.read())["groups"]
        return groups

def get_calendars_ids() -> list[str] | None:
    """
    Returns a list of the calendars' ids saved in data.json file

    @flag data
    @flag calendar
    """
    create_data_file()
    with open("data.json", "r") as f:
        data = json.loads(f.read())
        return data["calendar_ids"]

def add_calendar(calendar_id):
    """
    Adds calendar to data.json

    @flag data
    @flag calendar
    """
    create_data_file()
    if len(calendar_id) <= 5:
        return

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

    @flag data
    @flag calendar
    """
    create_data_file()
    with open("data.json", "r") as f:
        data = json.loads(f.read())
    with open("data.json", "w") as f:
        if calendar_id in data["calendar_ids"]:
            data["calendar_ids"].remove(calendar_id)
            f.write(json.dumps(data))

def get_admins() -> list[int]:
    """
    Returns a list of the admins' uuids

    @flag data
    """
    create_data_file()

    with open("data.json", "r") as f:
        admins = json.loads(f.read())["admins"]
        return admins


def add_admin(uuid: int):
    """
    Adds an admin to the data.json file

    @flag data
    """
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
    """
    Removes an admin from the data.json file

    @flag data
    """
    create_data_file()
    with open("data.json", "r") as f:
        data = json.loads(f.read())
    if data != None:
        with open("data.json", "w") as f:
            if uuid in data["admins"]:
                data["admins"].remove(uuid)
                f.write(json.dumps(data))

def get_owners() -> list[int]:
    """
    Returns a list of the owners' uuids

    @flag data
    """
    create_data_file()
    with open("data.json", "r") as f:
        owners = json.loads(f.read())["owners"]
        return owners

def add_owner(uuid: int):
    """
    Adds an owner to the data.json file

    @flag data
    """
    create_data_file()
    data = None
    with open("data.json", "r") as f:
        data = json.loads(f.read())
    if data != None:
        with open("data.json", "w") as f:
            if uuid not in data["owner"]:
                data["owner"].append(uuid)
                f.write(json.dumps(data))

def get_setlists_ids() -> list[str] | None:
    """
    Returns a list of the setlists' ids saved in data.json file

    @flag data
    @flag setlist
    """
    create_data_file()
    with open("data.json", "r") as f:
        data = json.loads(f.read())
        return [setlist[0] for setlist in data["setlists"]]

def add_setlist(setlist_id: str, name:str):
    """
    Adds a setlist id to the data.json file

    @flag data
    @flag setlist
    """
    create_data_file()
    if len(setlist_id) <= 5:
        return

    data = None
    with open("data.json", "r") as f:
        data = json.loads(f.read())
    if data != None:
        with open("data.json", "w") as f:
            if setlist_id not in data["setlists"]:
                data["setlists"].append([setlist_id, name, ""])
                f.write(json.dumps(data))

def get_setlist_name(setlist_id: str) -> str | None:
    """
    Returns the name of the setlist given its id

    @flag data
    @flag setlist
    """
    create_data_file()
    with open("data.json", "r") as f:
        data = json.loads(f.read())
        for setlist in data["setlists"]:
            if setlist[0] == setlist_id:
                return setlist[1]
    return None

def get_setlist_id_from_name(setlist_name: str) -> str | None:
    """
    Returns the setlist id given its name

    @flag data
    @flag setlist
    """
    create_data_file()
    with open("data.json", "r") as f:
        data = json.loads(f.read())
        for setlist in data["setlists"]:
            if setlist[1] == setlist_name:
                return setlist[0]
    return None

def get_setlist_calendar_url(setlist_id: str) -> str | None:
    """
    Returns the calendar of the setlist given its id

    @flag data
    @flag setlist
    @flag calendar
    """
    create_data_file()
    with open("data.json", "r") as f:
        data = json.loads(f.read())
        for setlist in data["setlists"]:
            if setlist[0] == setlist_id:
                return setlist[2]
    return None

def add_calendar_to_setlist(setlist_id: str, calendar_id: str):
    """
    Link a calendar to a given setlist

    @flag data
    @flag setlist
    @flag calendar
    """
    create_data_file()
    with open("data.json", "r") as f:
        data = json.loads(f.read())
    if data is not None:
        for setlist in data["setlists"]:
            if setlist[0] == setlist_id:
                setlist[2] = calendar_id
                break
        with open("data.json", "w") as f:
            f.write(json.dumps(data))

def remove_setlist(index: int):
    """
    Removes a setlist id from the data.json file

    @flag data
    @flag setlist
    """
    create_data_file()
    with open("data.json", "r") as f:
        data = json.loads(f.read())
    if data != None:
        with open("data.json", "w") as f:
            data["setlists"].pop(index)
            f.write(json.dumps(data))

def get_embed_colour()-> int:
    """
    Returns the embed color used for #TODO what is it for ?

    @flag data
    """
    create_data_file()
    with open("data.json", "r") as f:
        colour = json.loads(f.read())["embed_colour"]
        return colour

def change_embed_colour(colour: str):
    """
    Hexadecimal format

    @flag data
    """
    create_data_file()
    with open("data.json", "r") as f:
        data = json.loads(f.read())
    if data != None:
        with open("data.json", "w") as f:
            data["embed_colour"] = int(colour, 16)
            f.write(json.dumps(data))

def get_instruments_names_translation() -> dict:
    """
    Returns a dict for translating DB columns (keys) to spreadsheets column names (list of values)

    @flag data
    """
    instruments_file = {}
    create_data_file()
    with open("data.json", "r", encoding="utf-8") as f:
        instruments_file = json.load(f)["instruments"]

    return instruments_file

def get_ignored_column_names() -> dict:
    """
    Returns a list of ignored spreadsheet columns' names

    @flag data
    """
    data = {}
    if os.path.exists("data.json"):
        with open("data.json", "r", encoding="utf-8") as f:
            data = json.load(f)["ignored_columns"]

    return data

def add_ignored_column(column: str):
    """
    Adds a column name to the list of ignored columns in the data.json file

    @flag data
    """
    create_data_file()
    with open("data.json", "r") as f:
        data = json.loads(f.read())
    if data != None and column not in data["ignored_columns"]:
        with open("data.json", "w") as f:
            data["ignored_columns"].append(column)
            f.write(json.dumps(data))

def remove_ignored_column(column: str): #TODO integrate command
    """
    Removes a column name from the list of ignored columns in the data.json file

    @flag data
    """
    create_data_file()
    with open("data.json", "r") as f:
        data = json.loads(f.read())
    if data != None:
        with open("data.json", "w") as f:
            data["ignored_columns"].remove(column)
            f.write(json.dumps(data))

def add_instrument_translation(instrument: str, translation: str):
    """
    Adds an instrument translation to the data.json file

    @flag data
    """
    create_data_file()
    with open("data.json", "r") as f:
        data = json.loads(f.read())
    if data != None:
        with open("data.json", "w") as f:
            if instrument in list(data["instruments"].keys()):
                if translation not in data["instruments"][instrument]:
                    data["instruments"][instrument].append(translation)
            else:
                data["instruments"][instrument] = [translation]
            f.write(json.dumps(data))




###############################
#     Download operations     #
###############################

def download_timetables():
    """
    Downloads timetables as .ics files in ./timetables

    Do not forget to call db.update_timetables() to update the database!

    returns: True if operation successful 
    """
    r = subprocess.call(os.path.join("scripts","auto_update.sh"))
    return r == 0




#############################
#          Parsing          #
#############################

def parse_date(date: str) -> str:
    """
    Parses a date string and returns it in the YYYYMMDD format.

    @flag parsing
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
                raise ValueError(f"« {date} » n’est pas reconnu comme une date valide.")

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


    raise ValueError(f"« {date} » n’est pas reconnu comme une date valide.")

def parse_time(time_string: str) -> str:
    """
    Parses a time string and returns it in the HHMM format.

    @flag parsing
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

    raise ValueError(f"« {time_string} » n’est pas reconnu comme une heure valide.")

def parse_duration(duration: str) -> int:
    """
    Parses a duration string (precision up to minutes) and returns the corresponding duration in seconds.
    Format example: 30m, 1:30, 1h30, 1-30

    @flag parsing
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

    raise ValueError(f"« {duration} » n’est pas reconnu comme une durée valide.")

accent_data = {"Clement": "Clément",
               "Angele": "Angèle",
               "Gael": "Gaël",
               "Elea-rose": "Éléa-Rose",
               "Mohamed-emine": "Mohamed Emine",
               "Raphael": "Raphaël",
               "Elisa": "Élisa",
               "Kevin": "Kévin",
               "Etienne": "Étienne",
               "Zoe": "Zoé",
               "Theo": "Théo",
               "Chloe": "Chloé",
               "Andre": "André",
               "Noe": "Noé",
               "Cedric": "Cédric",
               "LIENARD": "LIÉNARD",
               "ESCUDE--COTINAT": "ESCUDE–COTINAT",
               "JIMENEZ--PIQUEMAL": "JIMENEZ–PIQUEMAL"
               }

def parse_mail(mail: str) -> str:
    """
    Returns the name of the owner of the mail address ([first_name].[last_name]@[...] format)

    @flag parsing
    """
    mail = mail.split("@")[0].split(".")

    if len(mail) != 2:
        return mail
    if mail[0].capitalize() in accent_data:
        mail[0] = accent_data[mail[0].capitalize()]
    else:
        mail[0] = mail[0].capitalize()

    if mail[1].upper() in accent_data:
        mail[1] = accent_data[mail[1].upper()]
    else:
        mail[1] = mail[1].upper()

    return mail[0] + " " + mail[1]




#########################################
#     User-friendly date formatting     #
#########################################

def get_special_date_string(date: str) -> str:
    """
    Returns a Markdown-formatted user-friendly string in french of the date given in argument.

    Note: might return 'Demain' and 'Aujourd'hui'

    Args:
        date (str): The date, in YYYYMMDD format

    @flag markdown
    @flag date_string
    @flag to_string
    """
    today = int(datetime.now().strftime("%Y%m%d"))

    if str(today) == date:
        return "**aujourd’hui**"

    if str(today + 1) == date:
        return "**demain**"

    if str(today + 2) == date:
        return "**après-demain**"

    try:
        return f"le **{date[-2:]}/{date[4:6]}/{date[:4]}**"
    except:
        raise ValueError(f"« {date} » n’est pas sous le format YYYYMMDD.")

def formatted_time_span_string(start: str, end: str) -> str:
    """
    Returns a Markdown-formatted user-friendly string in french of the time span given in argument

    Note: might return 'Toute la journée'.

    Args:
        start (str): The start time of the span, in HHMM format
        end (str): The end time of the span, in HHMM format

    @flag markdown
    @flag timespan_string
    @flag to_string
    """

    if len(start) != 4 or len(end) != 4:
        raise ValueError(f"« {start} » et/ou « {end} » n’est pas sous le format HHMM.")

    res = ""

    if start == "0000" and end == "2359":
        return "**toute la journée**"

    if start == "0000":
        res += "jusqu’"
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
    Returns a user-friendly string of a time span (epoch values)

    @flag markdown
    @flag timespan_string
    @flag to_string
    """
    return formatted_time_span_string(time.strftime("%H%M", time.gmtime(start_time)), time.strftime("%H%M", time.gmtime(end_time)))

def formatted_hhmm(time_string: str) -> str:
    """
    Returns a formal string in french of the time given in argument.

    Args:
        time (str): The time, in HHMM format

    @flag time_string
    @flag to_string
    @flag formal
    """

    if len(time_string) != 4:
        raise ValueError(f"« {time_string} » n’est pas sous le format HHMM.")

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
    Returns a string of the duration given in argument.

    Args:
        duration (int): The duration in seconds

    @flag to_string
    """
    res = ""
    if duration >= 3600:
        res += f"{int(duration/3600)} h"


    if duration%3600 != 0:
        if res:
            res += " "
        res += f"{int(duration%3600 / 60)} m"

    return res

def epoch_to_ddmm(epoch_time: int) -> str:
    """
    Returns the date in DD/MM format

    @flag to_string
    """
    return time.strftime("%d/%m", time.gmtime(epoch_time))

def get_constraint_description(constraint: list[int]) -> str:
    """
    Returns a user-friendly text for the corresponding constraint

    @flag to_string
    @flag constraint
    """
    return f"Indisponible {time_span_to_string(constraint[0], constraint[1])}\n"

def get_date_string(epoch_time: int) -> str:
    """
    Returns a string formatted like this: Jeudi 24/10

    @flag to_string
    """
    return f"{timeutils.week_index_to_week_day(time.gmtime(epoch_time).tm_wday + 1)} {epoch_to_ddmm(epoch_time)}"




#######################
#     Other works     #
#######################

def add_missing_recurring_constraints(message: str, constraints: list[list[int]], recurring_constraints: list[list[list[int]]], start_time: int, daynb: int, boundary: int) -> str:
    """
    When recurring constraints happen between the last and the next constraint of any other type, they may be missed

    This function makes sure no constraint is left behind
    """
    j = 0
    # Iterate through recurring constraints until boundary
    while timeutils.get_first_day_of_week(timeutils.get_nbweeks(start_time)) + j * timeutils.DAY_DURATION < boundary:
        if len(recurring_constraints[j]) > 0:
            # Write the day's date in case of a change of day number (which has to be updated after the call of the function (choose the boundary wisely))
            if timeutils.get_nbdays(timeutils.get_first_day_of_week(timeutils.get_nbweeks(start_time)) + j * timeutils.DAY_DURATION) != daynb: # TODO beware of the missing daynb update !
                message += "**" + "\n" + get_date_string(timeutils.get_first_day_of_week(timeutils.get_nbweeks(start_time)) + j * timeutils.DAY_DURATION) + "**\n"

            # Pop the recurring constraints
            while len(recurring_constraints[j]) > 0: #TODO no check for boundary might cause errors ?
                message += "🟦 " + get_constraint_description(recurring_constraints[j].pop(0))
        j += 1
    return message




#################################
#     Heavy string building     #
#################################

def get_constraints_week_description(constraints: list[list[int]], start_time: int) -> str:
    """
    Writes a message describing all musicians' constraints for the week of a given start time

    constraints: result of a db request as list of (start_time, end_time, week_day) from musician constraints sorted by start time
    start_time: epoch value of a day in the week
    """

    # Gets the week number to track for week change between constraints
    weeknb = timeutils.get_nbweeks(start_time)
    i = 0
    # List of all recurring contraints for the week, per day (recurrent ones are put directly in each day)
    recurring_constraints = [[],[],[],[],[],[],[]]

    # First, start from the first constraint and continue until getting the first constraint from the right week
    while i < len(constraints) and timeutils.get_nbweeks(constraints[i][0]) < weeknb:
        # At the beginning are all the recurring constraints
        if constraints[i][0] < timeutils.DAY_DURATION and constraints[i][2] > 0:
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
    while i < len(constraints) and timeutils.get_nbweeks(constraints[i][0]) < weeknb+1:
        # First, write the date
        # daynb == 0 means the message is empty (could also check for message == "")
        # The second test is for when the next constraint happens on another day
        if daynb == 0 or timeutils.get_nbdays(constraints[i][0]) > daynb:

            # Get recurring constraints happening after the last constraint and still int the previous day
            message = add_missing_recurring_constraints(message, constraints, recurring_constraints, start_time, daynb, (constraints[i][0] // timeutils.DAY_DURATION) * timeutils.DAY_DURATION)
            # Update the day tracker
            daynb = timeutils.get_nbdays(constraints[i][0])
            # Add the date of the day in the message
            message += "**" + "\n" + get_date_string(constraints[i][0]) + "**\n"

        # Now check for recurring constraint happening before the constraint
        if len(recurring_constraints[time.gmtime(constraints[i][0]).tm_wday]) > 0: # First check the day
            # Then check wether or not to write the recurring constraints
            j = len(recurring_constraints[time.gmtime(constraints[i][0]).tm_wday][0])
            while j > 0:
                if recurring_constraints[time.gmtime(constraints[i][0]).tm_wday][0][0] < constraints[i][0]%timeutils.DAY_DURATION:
                    message += "🟦 " + get_constraint_description(recurring_constraints[time.gmtime(constraints[i][0]).tm_wday].pop(0))
                    j = len(recurring_constraints[time.gmtime(constraints[i][0]).tm_wday][0])
                else:
                    j = 0

        # Finally, write the constraint
        message += "🟨 " + get_constraint_description(constraints[i])
        i+=1

    # In case of recurring constraints still happening after the last checked constraint, add them
    message = add_missing_recurring_constraints(message, constraints, recurring_constraints, start_time, daynb, timeutils.get_first_day_of_week(weeknb + 1))
    return message


def week_timetable_string_from_constraints(recurring_constraints: list[list], punctual_constraints: list[dict]) -> str:
    """
    Returns a string displaying a week's timetable given a list of recurring constraints and punctual constraints obtained from db.get_week_constraints_for_rehearsal()
    """
    message = "```"
    message += "       L M M J V S\n"
    for i in range(15):
        if i < 2:
            message += " "
        message += f"{i+8}h00 "
        for j in range(6):
            char = None
            if punctual_constraints[j]:
                for key in punctual_constraints[j].keys():
                    # print(punctual_constraint[j][key][0], punctual_constraint[j][key][2], key, i, i+8, (i+8)*3600)
                    # if starting in the next hour, or ending in the next hour, or starting before and ending after
                    if ((i+8)*3600 <= key and key < (i+8+1)*3600) or ((i+8) * 3600 < punctual_constraints[j][key][2] % timeutils.DAY_DURATION and punctual_constraints[j][key][2] % timeutils.DAY_DURATION <= (i + 8 + 1) * 3600) or ((i + 8) * 3600 > key and punctual_constraints[j][key][2] % timeutils.DAY_DURATION > (i + 8 + 1) * 3600):
                        if punctual_constraints[j][key][3] == 1:
                            # School event
                            char = "🟦"
                        elif punctual_constraints[j][key][3] == 2 and char is None:
                            # Google event
                            char = "🟨"
                        elif punctual_constraints[j][key][3] == 3 and char is None:
                            # Punctual Constraint
                            char = "🟥"
                        else:
                            if char is None:
                                char = "🟪"
            if char is None:
                for value in recurring_constraints[j]:
                    if (i + 8) * timeutils.DAY_DURATION <= value[1] and value[1] < (i + 8 + 1) * timeutils.DAY_DURATION:
                        char = "🟥"
            if char is None:
                char = "⬛"
            message += char
            message += ""
        message += "\n"
    message += "```"
    return message


def day_timetable_string_from_constraints(recurring_constraints: list[list], punctual_constraints: dict, cursor_col: int = 0) -> tuple[str, bool]:
    """
    Returns a tuple containing:
        - a string displaying a day's timetable given a list of recurring constraints and punctual constraints obtained from db.get_week_constraints_for_rehearsal()
        - a boolean indicating if the selected time slot is available or not
    """
    message = "```"
    constraints_strings = []
    slots = []
    available = False
    for i in range(15):
        if i < 2:
            message += " "
        char = None
        if punctual_constraints:
            for key in punctual_constraints.keys():
                # print(punctual_constraint[j][key][0], punctual_constraint[j][key][2], key, i, i+8, (i+8)*3600)
                # if starting in the next hour, or ending in the next hour, or starting before and ending after
                if ((i+8)*3600 <= key and key < (i+8+1)*3600) or ((i+8) * 3600 < punctual_constraints[key][2] % timeutils.DAY_DURATION and punctual_constraints[key][2] % timeutils.DAY_DURATION <= (i + 8 + 1) * 3600) or ((i + 8) * 3600 > key and punctual_constraints[key][2] % timeutils.DAY_DURATION > (i + 8 + 1) * 3600):
                    if punctual_constraints[key][3] == 1:
                        # School event
                        char = "🟦" if i != cursor_col else "🔵"
                    elif punctual_constraints[key][3] == 2 and char is None:
                        # Google event
                        char = "🟨" if i != cursor_col else "🟡"
                    elif punctual_constraints[key][3] == 3 and char is None:
                        # Punctual Constraint
                        char = "🟥" if i != cursor_col else "🔴"
                    else:
                        if char is None:
                            char = "🟪" if i != cursor_col else "🟣"
                    if i == cursor_col:
                        dot = None
                        if punctual_constraints[key][3] == 1:
                            # School event
                            dot = "🔵"
                        elif punctual_constraints[key][3] == 2:
                            # Google event
                            dot = "🟡"
                        elif punctual_constraints[key][3] == 3:
                            # Punctual Constraint
                            dot = "🔴"
                        else:
                            if dot is None:
                                char = "🟣"
                        constraint_string = f""" {dot} {time_span_to_string(punctual_constraints[key][1], punctual_constraints[key][2])} - {punctual_constraints[key][0] if punctual_constraints[key][3] != 3 else "Indisponible"}"""
                        if constraint_string not in constraints_strings:
                            constraints_strings.append(constraint_string)
        if char is None:
            for value in recurring_constraints:
                if (i + 8) * timeutils.DAY_DURATION <= value[1] and value[1] < (i + 8 + 1) * timeutils.DAY_DURATION:
                    char = "🟥" if i != cursor_col else "🔴"
                    constraint_string = f"""{char} {time_span_to_string(value[1], value[2])} - Indisponible"""

                    if i == cursor_col:
                        if constraint_string not in constraints_strings:
                            constraints_strings.append(constraint_string)
        if char is None:
            char = "⬛" if i != cursor_col else "⚫"

        slots.append(char)

    for slot in slots:
        message += slot
    message += "\n"

    message += f"------{'-' if cursor_col < 2 else ''}{cursor_col+8}h00------\n"

    for i in range(len(constraints_strings)):
        message += constraints_strings[i] + "\n"

    if len(constraints_strings) == 0:
        message += "Créneau disponible\n"
        available = True
    message += "```"
    return message, available
