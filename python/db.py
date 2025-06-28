import sqlite3
import time
import os
import python.driveutils as driveutils
db = sqlite3.connect("./database/database.db")

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

def duration(start: str, end:str) -> int:
    """
    Returns the duration between two ICS timestamps in minutes.
    """
    start_time = time.strptime(start, "%Y%m%dT%H%M%SZ")
    end_time = time.strptime(end, "%Y%m%dT%H%M%SZ")
    start_seconds = time.mktime(start_time)
    end_seconds = time.mktime(end_time)
    return int((end_seconds - start_seconds) / 60)

def update_timetables():

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
                            command += f"('{event['uuid']}', '{group}', '{event['start_time']}', '{event['end_time']}', '{duration(event['start_time'], event['end_time'])}'),"
                        else:
                            print("Incomplete event data, skipping insertion.")

                    elif line.startswith("UID:"):
                        event["uuid"] = line.split(":", 1)[1].strip()
                    elif line.startswith("DTSTART:"):
                        event["start_time"] = line.split(":", 1)[1].strip()
                    elif line.startswith("DTEND:"):
                        event["end_time"] = line.split(":", 1)[1].strip()

    command = command[:-1] + ";" # Remove the last comma and add a semicolon

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