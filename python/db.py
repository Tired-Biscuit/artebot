import sqlite3
import time
import os
import json
import python.driveutils as driveutils

# TODO faire des tests d'injection sur les champs de type : nom du morceau

if os.path.exists("./database/database.db"):
    db = sqlite3.connect("./database/database.db")
else:
    with open("./database/database.db", "w") as f:
        f.close()

# # # # # # # # # # # # # # #
#      Basic functions      #
# # # # # # # # # # # # # # #

def run(command):
    cursor = db.cursor()
    try:
        cursor.execute(command)
        db.commit()
        result = cursor.fetchall()
    except Exception as e:
        result = e
    finally:
        cursor.close()
    return result

def runscript(script):
    cursor = db.cursor()
    try:
        cursor.executescript(script)
        db.commit()
        result = cursor.fetchall()
    except Exception as e:
        result = e
    finally:
        cursor.close()
    return result

def reset():
    with open("./sql/reset.sql", "r") as f:
        content = f.read()
    return runscript(content)

def init():
    with open("./sql/init.sql", "r") as f:
        content = f.read()
    return runscript(content)

# # # # # # # # # # # # # # #
#    Database operations    #
# # # # # # # # # # # # # # #

def ics_to_unixepoch(ics_time: str) -> int:
    """
    Converts an ICS timestamp to a Unix epoch timestamp.
    """
    time_struct = time.strptime(ics_time, "%Y%m%dT%H%M%SZ")
    return int(time.mktime(time_struct))

def cal_to_unixepoch(cal_time: str) -> int:
    """
    Converts a Google Calendar timestamp to a Unix epoch timestamp.
    """
    time_struct = time.strptime(cal_time[:-6], "%Y-%m-%dT%H:%M:%S")
    return int(time.mktime(time_struct))

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
                            command += f"""('{event['uuid']}', '{group}', '{event['start_time']}', '{event['end_time']}', '{(event['end_time'] - event['start_time'])/60}', "{event['subject']}"),"""
                        else:
                            print("Incomplete event data, skipping insertion.")

                    elif line.startswith("UID:"):
                        event["uuid"] = line.split(":", 1)[1].strip()
                    elif line.startswith("DTSTART:"):
                        event["start_time"] = ics_to_unixepoch(line.split(":", 1)[1].strip())
                    elif line.startswith("DTEND:"):
                        event["end_time"] = ics_to_unixepoch(line.split(":", 1)[1].strip())
                    elif line.startswith("SUMMARY:"):
                        event["subject"] = line.split(":", 1)[1].strip()

    command = command[:-1] + ";" # Remove the last comma and add a semicolon

    return run(command)

def update_calendar(calendar):
    """
    Updates the database with the latest calendar events from the google calendars in data.json
    """
    
    command = "INSERT OR REPLACE INTO GoogleEvent VALUES"

    for event in calendar:
        keys = event.keys()
        if event and "id" in keys and "organizer" in keys and "start" in keys and "end" in keys and "summary" in keys and "location" in keys:
            if event["location"] in ["local", "Local", "LOCAL"]:
                musicians = ""
                if "attendees" in keys:
                    for attendee in event['attendees']:
                        musicians +=  f"""{attendee['email']} """
                    musicians = musicians[:-1]
                command += f"""('{event['id']}','{event['organizer']['email']}', "{musicians}", '{cal_to_unixepoch(event['start']['dateTime'])}', '{cal_to_unixepoch(event['end']['dateTime'])}', "{event['summary']}"),"""
        else:
            print("Incomplete event data, skipping insertion.")

    command = command[:-1] + ";" # Remove the last comma and add a semicolon

    return run(command)

def add_puncutal_constraint(musician, day, start_time, end_time):
    """
    Adds a constraint for a musician in the database.
    
    Args:
        musician (str): The UUID of the musician.
        day (str): The day of the constraint in DD-MM-YYYY format.
        start_time (str): THe start time of the constraint in HH:MM format.
        end_time (str): The end time of the constraint in HH:MM format.
    """
    command = f"INSERT INTO MusicianConstraint VALUES('{musician}', '{day}', '{start_time}', '{end_time}', 0);"
    return run(command)

def add_recurring_constraint(musician, start_time, end_time, week_day):
    """
    Adds a recurring constraint for a musician in the database.
    
    Args:
        musician (str): The UUID of the musician.
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

    command = f"INSERT INTO MusicianConstraint VALUES('{musician}', '', '{start_time}', '{end_time}', {day});"
    return run(command)

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