import sqlite3
import time
import os
import json
from inspect import stack

import python.googleutils as googleutils
import python.tools as tools
from fileinput import filename

from urllib3 import request

import python.driveutils as driveutils

# TODO faire des tests d'injection sur les champs de type : nom du morceau
# TODO ajouter la règle PRAGMA pour obliger l'unicité des Primary Keys
if os.path.exists("./database/database.db"):
    db = sqlite3.connect("./database/database.db")
else:
    with open("./database/database.db", "w") as f:
        pass

# # # # # # # # # # # # # # #
#      Basic functions      #
# # # # # # # # # # # # # # #

def run(command, *, commit=False):
    cursor = db.cursor()
    try:
        cursor.execute(command)
        db.commit()
        result = cursor.fetchall()
    except Exception as e:
        raise Exception(f"Error during request execution:\n            {e}\n\nWhen running the following request:\n\n{command}")
    finally:
        if commit:
            db.commit()
        cursor.close()
    return result

def runscript(script, *, allow_fail=False):
    cursor = db.cursor()
    try:
        cursor.executescript(script)
        db.commit()
        result = cursor.fetchall()
    except Exception as e:
        if not allow_fail:
            raise Exception(f"Error during script execution:\n            {e}\n\nWhen running the following script:\n\n{script}")
        else:
            return "Silenced error happened"
    finally:
        cursor.close()
    return result

def reset(*, allow_fail=False):
    with open("./sql/reset.sql", "r") as f:
        content = f.read()
    result = runscript(content, allow_fail=allow_fail)
    return result if result != [] else "Done"

def init():
    with open("./sql/init.sql", "r") as f:
        content = f.read()
    result = runscript(content)
    return result if result != [] else "Done"

# # # # # # # # # # # # # # #
#    Database operations    #
# # # # # # # # # # # # # # #

def update_timetables():
    """
    Updates the database with the latest timetables from .ics files in ./timetables.
    """
    if not os.path.exists("./timetables"):
        print("Timetables directory does not exist. Please create it and add .ics files.")
        return False

    command = "INSERT OR REPLACE INTO SchoolEvent VALUES"

    for filename in os.listdir("./timetables"):
        if filename.endswith(".ics"):

            group = filename[:-4] # Remove the .ics extension
            filepath = os.path.join("./timetables", filename)

            with open(filepath, "r") as file:
                for line in file:

                    if line.startswith("BEGIN:VEVENT"):
                        event = {}

                    elif line.startswith("END:VEVENT"):

                        if event and "uuid" in event and "start_time" in event and "end_time" in event:
                            command += f"""('{event['uuid']}', '{group}', '{event['start_time']}', '{event['end_time']}', '{(event['end_time'] - event['start_time'])/60}', "{event['name']}"),"""
                        else:
                            print("Incomplete event data, skipping insertion.")

                    elif line.startswith("UID:"):
                        event["uuid"] = line.split(":", 1)[1].strip()
                    elif line.startswith("DTSTART:"):
                        event["start_time"] = tools.ics_to_unixepoch(line.split(":", 1)[1].strip())
                    elif line.startswith("DTEND:"):
                        event["end_time"] = tools.ics_to_unixepoch(line.split(":", 1)[1].strip())
                    elif line.startswith("SUMMARY:"):
                        event["name"] = line.split(":", 1)[1].strip()

    command = command[:-1] + ";" # Remove the last comma and add a semicolon

    return run(command)

def update_calendar(calendar):
    """
    Updates the database with the latest calendar events from the google calendars in data.json
    """
    
    command = "INSERT OR REPLACE INTO GoogleEvent VALUES"

    for event in calendar:
        keys = event.keys()
        if event and "id" in keys and "organizer" in keys and "start" in keys and "end" in keys and "summary" in keys:
            if "location" in keys and event["location"] in ["local", "Local", "LOCAL"]:
                musicians = ""
                if "attendees" in keys:
                    for attendee in event['attendees']:
                        musicians +=  f"""{attendee['email']} """
                    musicians = musicians[:-1]
                if "dateTime" in event['start'].keys() and "dateTime" in event['end'].keys():
                    command += f"""('{event['id']}','{event['organizer']['email']}', "{musicians}", '{tools.cal_to_unixepoch(event['start']['dateTime'])}', '{tools.cal_to_unixepoch(event['end']['dateTime'])}', "{event['summary']}"),"""
        else:
            field_names = ["id", "organizer", "start", "end", "summary", "location"]
            missing_fields = ""
            for field_name in field_names:
                if field_name not in keys:
                    missing_fields += " "+field_name
            print(f"Incomplete event data, skipping insertion. Missing fields:{missing_fields}")

    if command != "INSERT OR REPLACE INTO GoogleEvent VALUES":
        command = command[:-1] + ";" # Remove the last comma and add a semicolon
        return run(command)

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
            print(f"Calendar update ({i}/{len(calendar_ids)}): {'Success' if (val := update_calendar(result[1])) in [[], None] else val}")

def add_user(uuid, email, group_id, *, commit=False):
    """
    Adds a user to the database.
    
    Args:
        uuid (str) : Discord user uuid
        email (str): The email of the musician.
        group_id (str): The group ID of the musician.
        commit (bool): (optional and keyword-only) ask for database commit on successful execution
    """

    command = f"INSERT INTO User VALUES({uuid}, '{email}', '{group_id}');"
    return run(command, commit=commit)

def add_punctual_constraint(musician_uuid: str, day: str, start_time: str, end_time: str):
    """
    Adds a constraint for a musician in the database.
    
    Args:
        musician (str): The UUID of the musician (Discord user uuid).
        day (str): The day of the constraint in DD-MM-YYYY format.
        start_time (str): The start time of the constraint in HH:MM format.
        end_time (str): The end time of the constraint in HH:MM format.
    """
    command = f"INSERT INTO MusicianConstraint VALUES('{musician_uuid}', '{day}', '{start_time}', '{end_time}', 0);"
    return run(command)


def add_new_punctual_constraint(musician_uuid: str, start_time: int, end_time: int):
    """
    Adds a constraint for a musician in the database.

    Args:
        musician (str): The UUID of the musician (Discord user uuid).
        start_time (int): The start time of the constraint in epoch
        end_time (int): The end time of the constraint in epoch
    """
    command = f"INSERT INTO MusicianConstraint VALUES('{musician_uuid}', '2025-01-01', '{start_time}', '{end_time}', 0);"
    return run(command)

def add_recurring_constraint(musician_uuid: str, start_time: str, end_time: str, week_day: int):
    """
    Adds a recurring constraint for a musician in the database.
    
    Args:
        musician (str): The UUID of the musician (Discord user uuid).
        start_time (str): THe start time of the constraint in HH:MM format.
        end_time (str): The end time of the constraint in HH:MM format.
        weekDay (int): The day of the week for the recurring event (1-8, where 1 is Monday, and 8 is every day).
    """
    days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    
    if week_day == "Tous" or week_day == "tous" or week_day == "tous les jours" or week_day == "Tous les jours":
        day = 8
    else:
        try:
            day = days.index(str.capitalize(week_day)) + 1
        except ValueError:
            raise ValueError(f"Invalid week day: {week_day}. Must be one of {days}.")

    command = f"INSERT INTO MusicianConstraint VALUES('{musician_uuid}', '', '{start_time}', '{end_time}', {day});"
    return run(command)


def add_new_recurring_constraint(musician_uuid: str, start_time: int, end_time: int, week_day: int):
    """
    Adds a recurring constraint for a musician in the database.

    Args:
        musician (str): The UUID of the musician (Discord user uuid).
        start_time (int): The start time of the constraint in epoch (in umber of seconds from 12:00 AM).
        end_time (int): The end time of the constraint in epoch.
        weekDay (int): The day of the week for the recurring event (1-8, where 1 is Monday, and 8 is every day).
    """

    command = f"INSERT INTO MusicianConstraint VALUES('{musician_uuid}', '', '{start_time}', '{end_time}', {week_day});"
    return run(command)

def request_constraints(musician_uuid: str) -> list[tuple]:
    """
    Returns all constraints from musician's Discord UUID
    """

    return run(f"SELECT start_time, end_time FROM MusicianConstraint WHERE musician_uuid == {musician_uuid}")

def request_blocking_events(time: int, duration: int, musician_id: str) -> list:
    """
    Returns the result of the request returning all events occuring at the given epoch time (or during the given duration in seconds), for the user with given uuid
    """
    return run(f"""
        SELECT name, start_time, end_time
        FROM (
            SELECT name, start_time, end_time
            FROM SchoolEvent
            JOIN User ON User.group_id = SchoolEvent.group_id
            WHERE User.uuid = {musician_id}
            
            UNION
            
            SELECT name, start_time, end_time
            FROM GoogleEvent
            JOIN User ON GoogleEvent.musicians LIKE '%' || User.email || '%'
            WHERE User.uuid = {musician_id}
            
            UNION
            
            SELECT week_day, start_time, end_time
            FROM MusicianConstraint
            JOIN User ON MusicianConstraint.musician_uuid = user.uuid
            WHERE User.uuid = {musician_id}
        ) AS Event
        WHERE (Event.start_time < {time} AND {time} < Event.end_time)
        OR (Event.start_time < {time+duration} AND {time+duration} < Event.end_time)
        OR ({time} <= Event.start_time AND Event.end_time <= {time+duration})
        ;
    """)

# # # # # # # # # # # # # # #
#     Outdated content      #
# # # # # # # # # # # # # # #


def insert_name(name):
    name = name.replace("'", " ")
    run(f"INSERT INTO Musique(Nom) VALUES('{name}');")

def add_field(field, value, name):
    value = value.replace("'", " ")
    name = name.replace("'", " ")
    run(f"UPDATE Musique SET {field} = '{value}' WHERE Nom == '{name}';")

def register_lines(lines):
    fields = lines[0]
    for line in lines:
        for i in range(len(line)):
            if i != 3:
                if i == 0:
                    insert_name(line[0])
                else:
                    add_field(fields[i], line[i], line[0])

def get_song(name):
    name = name.replace("'", " ")
    return run(f"SELECT * FROM Musique WHERE Nom == '{name}';")

def get_songs(name):
    songs = {}
    songs[trim_space(name)] = []
    try:
        result = run(f"SELECT * FROM Musique WHERE Chant LIKE '%{name}%' OR Guitare LIKE '%{name}%' OR Clavier LIKE '%{name}%' OR Batterie LIKE '%{name}%' OR Basse LIKE '%{name}%' OR Violon LIKE '%{name}%' OR Flûte LIKE '%{name}%' OR Saxo LIKE '%{name}%';")
        possible_matchs = []
        for song in result:
            for field in song:
                if (trim_space(name) == trim_space(field)):
                    if song not in songs[trim_space(name)]:
                        songs[trim_space(name)].append(song)
                elif (name in field) and (trim_space(field) != trim_space(name)) and ("&" not in field and "+" not in field):
                    if trim_space(field) not in songs.keys():
                        songs[trim_space(field)] = []
                    if song not in songs[trim_space(field)]:
                        songs[trim_space(field)].append(song)
                    if trim_space(field) not in possible_matchs:
                        possible_matchs.append(trim_space(field))
                elif ("&" in field):
                    for people in field.split("&"):
                        if (name in people) and (trim_space(people) != trim_space(name)):
                            if trim_space(people) not in songs.keys():
                                songs[trim_space(people)] = []
                            if song not in songs[trim_space(people)]:
                                songs[trim_space(people)].append(song)
                            if trim_space(people) not in possible_matchs:
                                possible_matchs.append(trim_space(people))
                elif ("+" in field):
                    for people in field.split("+"):
                        if (name in people) and (trim_space(people) != trim_space(name)):
                            if trim_space(people) not in songs.keys():
                                songs[trim_space(people)] = []
                            if song not in songs[trim_space(people)]:
                                songs[trim_space(people)].append(song)
                            if trim_space(people) not in possible_matchs:
                                possible_matchs.append(trim_space(people))
        text = ""
        for key in songs.keys():
            if len(songs[key]) > 0:
                text += f"{len(songs[key])} morceaux pour **{key}**:\n"
                for song in songs[key]:
                    text += get_song_infos(song, key)
                    text += "\n"
            text += "\n\n"
        result = text
        
    except Exception as e:
        result = str(e)
    return result

def update_db(force):
    if time.time() - tools.UPDATE_TIME < tools.DELTA_TIME and not force:
        return False
    else:
        driveutils.download_file_from_google_drive()
        reset()
        init()
        lines = update_lines()
        register_lines(lines)
        tools.UPDATE_TIME = time.time()
        return True