import sqlite3
import time
import os
import json

import python.googleutils as googleutils
import python.tools as tools
import python.timeutils as timeutils

# TODO faire des tests d'injection sur les champs de type : nom du morceau
# TODO ajouter la règle PRAGMA pour obliger l'unicité des Primary Keys

TESTING_DATABASE = False

database_path = os.path.join("database", "database.db")
testing_database_path = os.path.join("database", "testing_db.db")
init_path = os.path.join("sql", "init.sql")
reset_path = os.path.join("sql", "reset.sql")

if os.path.exists(database_path):
    db = sqlite3.connect(database_path)
else:
    db = None

class SongNotFoundError(Exception):
    def __init__(self):
        super().__init__("Could not find song")

class UserNotFoundError(Exception):
    def __init__(self):
        super().__init__("L’identifiant n’a pas pu être vérifié. Tente de t’enregistrer avec `/connexion`")

def refresh():
    """
    Refreshes the sqlite database instance
    """
    path = testing_database_path if TESTING_DATABASE else database_path
    global db
    if os.path.exists(path):
        db = sqlite3.connect(path)
    else:
        with open(path, "w") as f:
            pass




###########################
#     Basic functions     #
###########################

def run(command, data=None, *, commit=False):
    cursor = db.cursor()
    try:
        if data is None:
            cursor.execute(command)
        else:
            cursor.execute(command, data)
        db.commit()
        result = cursor.fetchall()
    except Exception as e:
        raise Exception(f"Error during request execution:\n            {e}\n\nWhen running the following request:\n\n{command}")
    finally:
        if commit:
            db.commit()
        cursor.close()
    return result


def run_many(command: str, data: list[tuple]):
    cursor = db.cursor()
    try:
        cursor.executemany(command, data)
        db.commit()
        result = cursor.fetchall()
    except Exception as e:
        raise Exception(f"Error during request execution:\n            {e}\n\nWhen running the following request:\n\n{command} with parameters:{data}")
    finally:
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
    with open(reset_path, "r") as f:
        content = f.read()
    result = runscript(content, allow_fail=allow_fail)
    return result if result != [] else "Done"


def init():
    with open(init_path, "r") as f:
        content = f.read()
    result = runscript(content)
    return result if result != [] else "Done"


if db is None:
    with open(database_path, "w") as f:
        f.write("")
        pass
    db = sqlite3.connect(database_path)
    init()


###############################
#     Database operations     #
###############################

def get_song_values(song: str) -> list | None:
    """
    Returns song info for given title
    """
    song_info = run("""SELECT * FROM Song WHERE title LIKE ?;""", ("%"+song+"%",))
    if song_info != []:
        return song_info[0]
    else:
        raise SongNotFoundError


def update_timetables():
    """
    Updates the database with the latest timetables from .ics files in ./timetables.
    """
    if not os.path.exists("timetables"):
        print("Timetables directory does not exist. Please create it and add .ics files.")
        return False

    data = []

    subgroups = 0 # bit-wise data: 0b01 = subgroup 1, 0b10 = subgroup 2, 0b11 = subgroups 1 & 2
    desc = ""

    groups_ids = list(tools.get_groups().values())

    for filename in os.listdir("timetables"):
        if filename.endswith(".ics"):

            group = filename[:-4] # Remove the .ics extension
            filepath = os.path.join("timetables", filename)

            with open(filepath, "r") as file:
                for line in file:

                    if line.startswith("BEGIN:VEVENT"):
                        event = {}

                    elif line.startswith("END:VEVENT"):
                        if event and "name" in event and "Langues Etrangères LV2" in event["name"]:
                            pass
                        else:
                            if event and "uuid" in event and "start_time" in event and "end_time" in event:
                                if subgroups & 1 == 1:
                                    data.append((event['uuid'], group+"1", event['start_time'], event['end_time'], (event['end_time'] - event['start_time'])/60, event['name']))
                                if subgroups & 2 == 2:
                                    data.append((event['uuid'], group+"2", event['start_time'], event['end_time'], (event['end_time'] - event['start_time'])/60, event['name']))
                                if subgroups == 0:
                                    data.append((event['uuid'], group+"0", event['start_time'], event['end_time'], (event['end_time'] - event['start_time'])/60, event['name']))
                            else:
                                print("Incomplete event data, skipping insertion.")
                        subgroups = 0

                    elif line.startswith("DESCRIPTION:"):
                        if group+"1" in line:
                            subgroups += 1
                        if group+"2" in line:
                            subgroups += 2
                        if group+"1" not in line and group+"2" not in line:
                            if group+"0" in groups_ids:
                                subgroups = 0
                            else:
                                subgroups = 3

                    elif line.startswith("UID:"):
                        event["uuid"] = line.split(":", 1)[1].strip()
                    elif line.startswith("DTSTART:"):
                        event["start_time"] = timeutils.ics_to_epoch(line.split(":", 1)[1].strip())
                    elif line.startswith("DTEND:"):
                        event["end_time"] = timeutils.ics_to_epoch(line.split(":", 1)[1].strip())
                    elif line.startswith("SUMMARY:"):
                        event["name"] = line.split(":", 1)[1].strip()

    command = "INSERT OR REPLACE INTO SchoolEvent VALUES(?,?,?,?,?,?);"

    return run_many(command, data)


def update_calendar(calendar):
    """
    Updates the database with the latest calendar events from the google calendars in data.json
    """


    data = []

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
                    data.append((event['id'], event['organizer']['email'], musicians, timeutils.gcal_to_epoch(event['start']['dateTime']), timeutils.gcal_to_epoch(event['end']['dateTime']), event['summary']))
        else:
            field_names = ["id", "organizer", "start", "end", "summary", "location"]
            missing_fields = ""
            for field_name in field_names:
                if field_name not in keys:
                    missing_fields += " "+field_name
            print(f"Incomplete event data, skipping insertion. Missing fields:{missing_fields}")

    command = "INSERT OR REPLACE INTO GoogleEvent VALUES(?,?,?,?,?,?);"
    return run_many(command, data)


def update_calendars():
    """
    Downloads Google Calendars in data.json and updates the database
    """
    calendar_ids = tools.get_calendars_ids()

    i=0
    for calendar_id in calendar_ids:
        i+=1
        result = googleutils.download_calendar(calendar_id)
        if result[0] and len(result[1]) > 0:
            print(f"Calendar update ({i}/{len(calendar_ids)}): {'Success' if (val := update_calendar(result[1])) in [[], None] else val}")
        else:
            print(f"No event in calendar {i}.")


def add_user(uuid: int, username: str, email: str, group_id: str, *, commit=False):
    """
    Adds a user to the database.

    Args:
        uuid (str) : Discord user uuid
        username (str) : The username of the musician.
        email (str): The email of the musician.
        group_id (str): The group ID of the musician.
        commit (bool): (optional and keyword-only) ask for database commit on successful execution
    """

    command = """INSERT INTO User VALUES(?,?,?,?);"""
    data = (uuid, username, email, group_id)
    return run(command, data, commit=commit)


def get_users() -> list[list] | None:
    result = run("""SELECT uuid, username, email, group_id FROM User;""")

    if result:
        return result


def get_owners() -> list[list] | None:
    owners_uuid = tools.get_owners()

    result = []

    for uuid in owners_uuid:
        info = run("""SELECT username, email FROM User WHERE uuid = ?;""", (uuid,))
        if info:
            result.append(info[0])

    if result:
        return result


def get_user_name(musician_uuid: int) -> str:
    try:
        u = run("""SELECT username FROM User WHERE uuid = ?;""", (musician_uuid,))[0][0]
    except Exception:
        raise Exception(f"Could not find user with id {musician_uuid}")
    return u


def get_user_name_from_email(email: str) -> str:
    try:
        u = run("""SELECT username FROM User WHERE email = ?;""",(email,))[0][0]
    except:
        u = tools.parse_mail(email)
    return u
        # raise Exception(f"""Erreur: lors de l'exécution de "SELECT username FROM User WHERE email = '{email}';" : {run(f"SELECT username FROM User WHERE email = '{email}';")}""")


def add_punctual_constraint(musician_uuid: int, start_time: int, end_time: int):
    """
    Adds a constraint for a musician in the database.

    Args:
        musician (str): The UUID of the musician (Discord user uuid).
        start_time (int): The start time of the constraint in epoch
        end_time (int): The end time of the constraint in epoch
    """
    command = """INSERT INTO MusicianConstraint VALUES(?,?,?,?,?);"""
    data = (musician_uuid, 0, start_time, end_time, 0)
    return run(command, data)


def add_recurring_constraint(musician_uuid: int, start_time: int, end_time: int, week_day: int):
    """
    Adds a recurring constraint for a musician in the database.

    Args:
        musician (int): The UUID of the musician (Discord user uuid).
        start_time (int): The start time of the constraint in epoch (in umber of seconds from 12:00 AM).
        end_time (int): The end time of the constraint in epoch.
        weekDay (int): The day of the week for the recurring event (1-8, where 1 is Monday, and 8 is every day).
    """

    command = """INSERT INTO MusicianConstraint VALUES(?,?,?,?,?);"""
    data = (musician_uuid, 0, start_time, end_time, week_day)
    return run(command, data)


def request_constraints(musician_uuid: int) -> list[list[int]]:
    """
    Returns start_time, end_time, week_day of constraints from musician's Discord UUID ordered by time
    """

    constraints: list[list[int]] = run("""SELECT start_time, end_time, week_day FROM MusicianConstraint WHERE musician_uuid == ? ORDER BY start_time ASC, week_day ASC;""", (musician_uuid,))
    if not constraints:
        raise ValueError(f"Pas de contraintes trouvées.")
    else:
        return constraints


def request_blocking_events(timestamp: int, duration: int, musician_id: int) -> list:
    """
    Returns the result of the request returning all events occuring at the given epoch time (or during the given duration in seconds), for the user with given uuid

    list of [label: str, start_time: int, end_time: int, event_type: bool]

    """
    return run(f"""
        SELECT name, start_time, end_time, event_type
        FROM (
            SELECT name, start_time, end_time, {tools.EVENT_TYPES["School"]} as event_type
            FROM SchoolEvent
            JOIN User ON User.group_id = SchoolEvent.group_id
            WHERE User.uuid = {musician_id}

            UNION

            SELECT name, start_time, end_time, {tools.EVENT_TYPES["Google"]} as event_type
            FROM GoogleEvent

            UNION

            SELECT week_day, start_time, end_time, {tools.EVENT_TYPES["Constraint"]} as event_type
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
        OR (Event.start_time < {timeutils.DAY_DURATION} AND (
            (Event.start_time < {timestamp%timeutils.DAY_DURATION} AND {timestamp%timeutils.DAY_DURATION} < Event.end_time)
            OR (Event.start_time < {timestamp%timeutils.DAY_DURATION + duration} AND {timestamp%timeutils.DAY_DURATION + duration} < Event.end_time)
            OR ({timestamp%timeutils.DAY_DURATION} <= Event.start_time AND Event.end_time <= {timestamp%timeutils.DAY_DURATION + duration})
        ))
        ;
    """)


def get_all_musicians_uuids_for_song(song: str) -> tuple[list[int], list[str]]:
    """
    Returns a tuple containing all registered uuids and all unregistered user emails in a song.
    """
    song_info = get_song_values(song)

    musicians_uuids = []
    unregistered_users = []
    for field in song_info[5:]:
        for email in field.split(" "):
            if len(email) > 17:  # TODO valid email
                value = run("""SELECT uuid FROM User WHERE email = ?;""", (email,))
                if len(value) > 0:
                    musicians_uuids.append(int(value[0][0]))
                else:
                    unregistered_users.append(email)
    return musicians_uuids, unregistered_users


def get_week_constraints_for_rehearsal(song: str, start_time: int = None) -> tuple[list[list], list[dict]]:
    """
    Returns a list of recurring constraints for each day of a week, and a list of punctual events for each day as a dictionary with start time as key

    (recurring, punctual)
    """
    evening_time = 22*3600
    # Fetch musicians' emails

    result = get_all_musicians_uuids_for_song(song)

    musicians_uuids = result[0]
    unregistered_users = result[1]

    # Get the current time
    start_time = int((time.time()//3600+1)*3600) if start_time is None else start_time

    # if start_time%timeutils.DAY_DURATION >= evening_time:
        # start_time = int((start_time//timeutils.DAY_DURATION + 1)*timeutils.DAY_DURATION + 8*3600) # The next day at 8 AM

    start_time = timeutils.get_first_day_of_week(timeutils.get_nbweeks(start_time))

    punctual_events = [{} for i in range(7)]
    recurring_events = [[] for i in range(7)]

    for weekdaynb in range(0, 6):
        for musician_uuid in musicians_uuids:
            events = request_blocking_events(start_time, timeutils.DAY_DURATION, musician_uuid)
            for event in events:
                if event[1] >= start_time:
                    if event[1] not in list(punctual_events[weekdaynb].keys()) or event[3] == 1:
                        punctual_events[weekdaynb][event[1]%timeutils.DAY_DURATION] = event
                else:
                    recurring_events[weekdaynb].append(event)
        start_time += timeutils.DAY_DURATION
    return recurring_events, punctual_events


def get_day_constraints_for_rehearsal(song: str, start_time: int = None) -> tuple[list[list], dict]:
    """
    Returns a list of recurring constraints for a day starting from the time given in paramter, and punctual events for the day as a dictionary with start time as key

    (recurring, punctual)
    """
    evening_time = 22*3600
    # Fetch musicians' emails

    result = get_all_musicians_uuids_for_song(song)

    musicians_uuids = result[0]
    unregistered_users = result[1]

    # Get the current time
    start_time = int((time.time()//3600+1)*3600) if start_time is None else start_time

    # if start_time%timeutils.DAY_DURATION >= evening_time:
        # start_time = int((start_time//timeutils.DAY_DURATION + 1)*timeutils.DAY_DURATION + 8*3600) # The next day at 8 AM

    # start_time = timeutils.get_first_day_of_week(timeutils.get_nbweeks(start_time))

    punctual_events = {}
    recurring_events = []

    for musician_uuid in musicians_uuids:
        events = request_blocking_events(start_time, timeutils.DAY_DURATION - start_time%(timeutils.DAY_DURATION), musician_uuid)
        for event in events:
            if event[1] >= start_time:
                if event[1] not in list(punctual_events.keys()) or event[3] == 1:
                    punctual_events[event[1]%timeutils.DAY_DURATION] = event
            else:
                recurring_events.append(event)
    start_time += timeutils.DAY_DURATION
    return recurring_events, punctual_events


def add_song(song: dict, db_columns: list[str]):
    """
    Adds a song int the database in the format of a dictionnary with each field set up to the database
    """

    if song["title"] == "":
        return

    columns = "("
    values = "("
    data = []
    for key in song.keys():
        columns += f"{key},"
        values += "?,"
        data.append(song[key])
    columns = columns[:-1] + ")"
    values = values[:-1] + ")"

    return run(f"""INSERT INTO Song {columns} VALUES {values};""", data)


def add_setlist(setlist_id: str, rows: int):
    """
    Adds all musics in a setlist to the database
    """
    data = googleutils.get_spreadsheet_data(setlist_id, rows)
    data = data["sheets"][0]["data"][0]
    rows = data["rowData"]
    column_names = googleutils.get_row_text(rows[0])

    db_columns = []
    for col in run("PRAGMA table_info(Song);"):
        db_columns.append(col[1])

    rows = rows[1:]
    for row in rows:
        add_song(googleutils.get_song_info_from_row_values(row["values"], setlist_id, column_names, db_columns), db_columns)


def get_song_columns_names() -> list[str]:
    """
    Returns a list of all the column names of the Song table in french (including non-instrument columns)

    @flag data
    """
    column_names = run("PRAGMA table_info(Song);")

    with open(tools.datafile_path, "r", encoding="utf-8") as f:
            instruments = json.load(f)["instruments"]

    return [instruments[column[1]] if column[1] in instruments else None for column in column_names]


def get_songs_message(musician_uuid: int, display:int) -> str:
    email = ""

    email = run("""SELECT email FROM User WHERE uuid = ?;""", (musician_uuid,))
    email = email[0][0]

    result = run("""
        SELECT * FROM Song
        WHERE voice LIKE :email
        OR guitar LIKE :email
        OR keys LIKE :email
        OR drums LIKE :email
        OR bass LIKE :email
        OR violin LIKE :email
        OR cello LIKE :email
        OR contrabass LIKE :email
        OR accordion LIKE :email
        OR flute LIKE :email
        OR saxophone LIKE :email
        OR brass LIKE :email;
    """, {"email":f"%{email}%"})
    if not result:
        return "Aucun morceau trouvé !"
    if len(result) == 1:
        text = f"1 morceau trouvé :\n"
    else:
        text = f"{len(result)} morceaux trouvés :\n"
    instruments_names = get_song_columns_names()

    if display == 2:
        for song in result:
            text += f"### {song[1]} — {song[2]} (*{tools.get_setlist_name(song[0])}*)\n"
            for i in range(5, len(song)):
                if song[i]:
                    text += "- "
                    if email in song[i]:
                        text += f"**"
                    text += f"{instruments_names[i][0].capitalize()} :"
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
                text += f"- **{song[1]}** :"
            else:
                text += f"### {song[1]} — {song[2]} (*{tools.get_setlist_name(song[0])}*)\n- "

            musician_list = list()
            for i in range(5, len(song)):
                    if song[i]:
                        musicians = song[i].split(" ")

                        if email in song[i]:
                            text += f" {instruments_names[i][0]}" if display == 0 else f" {instruments_names[i][0].capitalize()}"
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


def get_song_info_message(song: str) -> tuple:
    """
    Returns a summary of a song from its title
    """
    song_info = get_song_values(song)

    instruments_names = get_song_columns_names()

    text = f"*Setlist : {tools.get_setlist_name(song_info[0])}*\n"

    for i in range(5, len(song_info)):
        if song_info[i]:
            text += f"- {instruments_names[i][0].capitalize()} :"
            musicians = song_info[i].split(" ")
            for musician in musicians:
                text += f" {get_user_name_from_email(musician)},"
            text = text[:-1]
            text += "\n"

    return f"{song_info[1]} — {song_info[2]}", text


def get_profile_message(musician_uuid: int) -> str:
    """
    Returns a summary for a musician from its uuid
    """

    groups = tools.get_groups()


    info = run("""SELECT username, email, group_id FROM User WHERE uuid = ?;""", (musician_uuid,))
    info = info[0]

    email = info[1]
    number_of_songs = run("""
            SELECT COUNT(*) FROM Song
            WHERE voice LIKE :email
            OR guitar LIKE :email
            OR keys LIKE :email
            OR drums LIKE :email
            OR bass LIKE :email
            OR violin LIKE :email
            OR cello LIKE :email
            OR contrabass LIKE :email
            OR accordion LIKE :email
            OR flute LIKE :email
            OR saxophone LIKE :email
            OR brass LIKE :email;
        """, {"email":f"%{email}%"})[0][0]

    number_of_constraints = run("""SELECT COUNT(*) FROM MusicianConstraint WHERE musician_uuid = ?;""", (musician_uuid,))[0][0]

    group_text = ""
    if info[2]:
        for group in groups:
            if groups[group] == info[2]:
                group_text = group[:-1] if group[-1] == "0" else group
                break
    else:
        group_text = "extérieur"

    if not group_text:
        raise ValueError("Group does not exist")

    return f"""- Pseudo : **{info[0]}**\n
               - Email : **{info[1]}**\n
               - Groupe : **{group_text}**\n
               - Nombre de morceaux : **{number_of_songs}**\n
               - Nombre de contraintes ajoutées : **{number_of_constraints}**
            """


def get_song_musicians(song: list) -> tuple[list[int], list[int]]:
    """""
    Returns a list of IDs of musicians playing on the song, as well as a list of muscians not in the database
    """
    musicians = list()
    not_in_db = list()

    for inst in song[5:]:
        for musician in inst.split(" "):

            if musician:
                uuid = run("""SELECT uuid FROM User WHERE email = ?;""", (musician,))

                if uuid and uuid[0][0] not in musicians:
                    musicians.append(uuid[0][0])

                if not uuid and musician not in not_in_db:
                    not_in_db.append(musician)

    return musicians, not_in_db


def remove_constraint(musician_uuid:int, start_time: int, end_time: int, week_day: int):
    run("""DELETE FROM MusicianConstraint WHERE musician_uuid = ? AND start_time = ? AND end_time = ? AND week_day = ?;""", (musician_uuid, start_time, end_time, week_day))


def add_instrument(instrument: str, translation: str):
    db_columns = []
    for col in run("PRAGMA table_info(Song);"):
        db_columns.append(col[1])
    if instrument not in db_columns:
        run(f"""ALTER TABLE Song ADD {instrument} TEXT NOT NULL DEFAULT '';""")
    tools.add_instrument_translation(instrument, translation)


def get_rehearsals(user_id: int):
    events = run(f"""
    SELECT name, start_time, end_time, {tools.EVENT_TYPES["Google"]} as event_type
    FROM GoogleEvent
    JOIN User ON GoogleEvent.musicians LIKE '%' || User.email || '%'
    WHERE User.uuid = ?
    """, (user_id,))
    return events

def cleanup():
    """
    Cleans any outdated content in the database
    """
    setlist_ids = tools.get_setlists_ids()
    placeholders = ', '.join(['?'] * len(setlist_ids))
    run(f"DELETE FROM Song WHERE setlist_id NOT IN ({placeholders});", setlist_ids)


#############################
#     Discord utilities     #
#############################

def check_user(user_id: int) -> str:
    """
    Checks if the user is registered and raises user-friendly errors
    Also returns the username if successful
    """
    try:
        return get_user_name(user_id)
    except:
        raise UserNotFoundError
