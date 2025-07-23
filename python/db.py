import sqlite3
import time
import os
import json
import traceback
from inspect import stack

import python.googleutils as googleutils
import python.tools as tools

from urllib3 import request

import python.driveutils as driveutils

# TODO faire des tests d'injection sur les champs de type : nom du morceau
# TODO ajouter la règle PRAGMA pour obliger l'unicité des Primary Keys

TESTING_DATABASE = False

if os.path.exists("./database/database.db"):
    db = sqlite3.connect("./database/database.db")
else:
    with open("./database/database.db", "w") as f:
        pass

def refresh():
    """
    Refreshes the sqlite database instance
    """
    path = "./database/testing_db.db" if TESTING_DATABASE else "./database/db.db"
    global db
    if os.path.exists(path):
        db = sqlite3.connect(path)
    else:
        with open(path, "w") as f:
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
    if not os.path.exists("data.json"):
        print("No calendars added.")
        return False

    with open("data.json") as f:
        calendar_ids = json.loads(f.read())["calendar_ids"]
        if len(calendar_ids) == 0:
            print("/!\ Empty calendar list")
            return False
    i=0
    for calendar_id in calendar_ids:
        i+=1
        result = googleutils.download_calendar(calendar_id)
        if result[0] and len(result[1]) > 0:
            print(f"Calendar update ({i}/{len(calendar_ids)}): {'Success' if (val := update_calendar(result[1])) in [[], None] else val}")

def add_user(uuid, username, email, group_id, *, commit=False):
    """
    Adds a user to the database.
    
    Args:
        uuid (str) : Discord user uuid
        username (str) : The username of the musician.
        email (str): The email of the musician.
        group_id (str): The group ID of the musician.
        commit (bool): (optional and keyword-only) ask for database commit on successful execution
    """

    command = f"INSERT INTO User VALUES({uuid}, '{username}', '{email}', '{group_id}');"
    return run(command, commit=commit)

def get_user_name(musician_uuid: int):
    try:
        u = run(f"SELECT username FROM User WHERE uuid = {musician_uuid};")[0][0]
    except Exception:
        raise Exception("Tu ne te trouves pas dans la base de données.")
    return u

def get_user_name_from_email(email: str) -> str:
    try:
        u = run(f"SELECT username FROM User WHERE email = '{email}';")[0][0]
    except:
        u = tools.parse_mail(email)
    return u
        # raise Exception(f"""Erreur: lors de l'exécution de "SELECT username FROM User WHERE email = '{email}';" : {run(f"SELECT username FROM User WHERE email = '{email}';")}""")


def add_punctual_constraint(musician_uuid: str, start_time: int, end_time: int):
    """
    Adds a constraint for a musician in the database.

    Args:
        musician (str): The UUID of the musician (Discord user uuid).
        start_time (int): The start time of the constraint in epoch
        end_time (int): The end time of the constraint in epoch
    """
    command = f"INSERT INTO MusicianConstraint VALUES('{musician_uuid}', '2025-01-01', '{start_time}', '{end_time}', 0);"
    return run(command)


def add_recurring_constraint(musician_uuid: str, start_time: int, end_time: int, week_day: int):
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

def request_blocking_events(timestamp: int, duration: int, musician_id: str) -> list:
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
            AND (MusicianConstraint.week_day = 0
            OR MusicianConstraint.week_day = 8
            OR MusicianConstraint.week_day = {time.gmtime(timestamp).tm_wday+1}
            )
        ) AS Event
        WHERE (Event.start_time < {timestamp} AND {timestamp} < Event.end_time)
        OR (Event.start_time < {timestamp + duration} AND {timestamp + duration} < Event.end_time)
        OR ({timestamp} <= Event.start_time AND Event.end_time <= {timestamp + duration})
        OR (Event.start_time < {tools.DAY_DURATION} AND (
            TRUE OR
            (Event.start_time < {timestamp%tools.DAY_DURATION} AND {timestamp%tools.DAY_DURATION} < Event.end_time)
            OR (Event.start_time < {timestamp%tools.DAY_DURATION + duration} AND {timestamp%tools.DAY_DURATION + duration} < Event.end_time)
            OR ({timestamp%tools.DAY_DURATION} <= Event.start_time AND Event.end_time <= {timestamp%tools.DAY_DURATION + duration})
        ))
        ;
    """)

def add_song(song: dict):
    """
    Adds a song in the format of a dictionnary with each field set up to the database
    """

    return run(f"""INSERT INTO
    Song ('title', 'artist', 'length', 'supervisor', 'voice', 'guitar', 'keys', 'drums', 'bass', 'violin', 'cello', 'contrabass', 'accordion', 'flute', 'saxophone', 'brass', 'notes')
    VALUES ("{song['title']}", "{song['artist']}", "{song['length']}", "{song['supervisor']}", "{song['voice']}", "{song['guitar']}", "{song['keys']}", "{song['drums']}",
    "{song['bass']}", "{song['violin']}", "{song['cello']}", "{song['contrabass']}", "{song['accordion']}", "{song['flute']}", "{song['saxophone']}", "{song['brass']}", "{song['notes']}"
);""")

def add_setlist(setlist_id: str, rows: int):
    data = googleutils.get_spreadsheet_data(setlist_id, rows)
    data = data["sheets"][0]["data"][0]
    rows = data["rowData"]
    for row in rows:
        add_song(googleutils.get_song_info_from_row_values(row["values"]))


def get_instruments_names() -> list[str]:
    """
    Returns a list of all the column names of the Song table in french (including non-instrument columns)
    """
    instruments = run("PRAGMA table_info(SONG);")

    with open("./instruments.json", "r", encoding="utf-8") as f:
            instruments_file = json.load(f)

    return [instruments_file[instrument[1]] if instrument[1] in instruments_file else None for instrument in instruments]



def get_songs_message(musician_uuid: int, display:int) -> str:
    email = ""
    try:
        email = run(f"SELECT email FROM User WHERE uuid = '{musician_uuid}'")
        email = email[0][0]
    except Exception as e:
        raise Exception(f"Could not get email: {e.with_traceback(None)}")

    try:
        result = run(f"""
            SELECT * FROM Song
            WHERE voice LIKE '%{email}%'
            OR guitar LIKE '%{email}%'
            OR keys LIKE '%{email}%'
            OR drums LIKE '%{email}%'
            OR bass LIKE '%{email}%'
            OR violin LIKE '%{email}%'
            OR cello LIKE '%{email}%'
            OR contrabass LIKE '%{email}%'
            OR accordion LIKE '%{email}%'
            OR flute LIKE '%{email}%'
            OR saxophone LIKE '%{email}%'
            OR brass LIKE '%{email}%';
        """)
        if not result:
            return "Aucun morceau trouvé !"
        if len(result) == 1:
            text = f"1 morceau trouvé :\n"
        else:
            text = f"{len(result)} morceaux trouvés :\n"
        instruments_names = get_instruments_names()


        if display == 2:

            for song in result:
                text += f"### {song[0]} — {song[1]}\n"
                for i in range(4, len(song)-1):
                    if song[i]:
                        text += "- "
                        if email in song[i]:
                            text += f"**"
                        text += f"{instruments_names[i].capitalize()} :"
                        if email in song[i]:
                            text += f"**"
                        musicians = song[i].split(" ")
                        for musician in musicians:
                            text += f" {get_user_name_from_email(musician)},"
                        text = text[:-1]
                        text += "\n"
        
        else:

            for song in result:

                if display == 0:
                    text += f"- **{song[0]}** :"
                else:
                    text += f"### {song[0]} — {song[1]}\n- "
                
                musician_list = list()
                for i in range(4, len(song)-1):
                        if song[i]:
                            musicians = song[i].split(" ")

                            if email in song[i]:
                                text += f" {instruments_names[i]}" if display == 0 else f" {instruments_names[i].capitalize()}"
                                if len(musicians) >= 2:
                                    text += f" (avec"
                                    for musician in musicians:
                                        if musician != email:
                                            text += f" {get_user_name_from_email(musician)},"
                                    text = text[:-1] + ")"
                                text += ","
                            
                            musician_list += [musician for musician in musicians if musician not in musician_list]

                text = text[:-1]
                if display == 1:
                    text += "\n- Membres :"
                    for musician in musician_list:
                        text += f" {get_user_name_from_email(musician)},"
                    text = text[:-1]
                text += "\n"

        return text
    except Exception:
        return traceback.format_exc()
    

with open("groups.json", "r", encoding="utf-8") as f:
        groups = json.load(f)

def get_profile_message(musician_uuid: int) -> str:
    try:
        info = run(f"SELECT username, email, group_id FROM User WHERE uuid = '{musician_uuid}'")
        info = info[0]
    except Exception as e:
        raise Exception(f"Could not get email: {e.with_traceback(None)}")
    
    email = info[1]
    number_of_songs = run(f"""
            SELECT COUNT(*) FROM Song
            WHERE voice LIKE '%{email}%'
            OR guitar LIKE '%{email}%'
            OR keys LIKE '%{email}%'
            OR drums LIKE '%{email}%'
            OR bass LIKE '%{email}%'
            OR violin LIKE '%{email}%'
            OR cello LIKE '%{email}%'
            OR contrabass LIKE '%{email}%'
            OR accordion LIKE '%{email}%'
            OR flute LIKE '%{email}%'
            OR saxophone LIKE '%{email}%'
            OR brass LIKE '%{email}%';
        """)[0][0]

    number_of_constraints = run(f"SELECT COUNT(*) FROM MusicianConstraint WHERE musician_uuid = {musician_uuid}")[0][0]

    group_text = ""
    if info[2]:
        for group in groups:
            if groups[group] == info[2]:
                group_text = group
                break
    else:
        group_text = "extérieur"

    if not group_text:
        raise ValueError("Groupe non existant")
    
    return f"""- Pseudo : **{info[0]}**\n
               - Email : **{info[1]}**\n
               - Groupe : **{group_text}**\n
               - Nombre de morceaux : **{number_of_songs}**\n
               - Nombre de contraintes ajoutées : **{number_of_constraints}**
            """
