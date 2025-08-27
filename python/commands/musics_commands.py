import discord
import time

import python.db as db
import python.tools as tools
import python.discordutils as discordutils
import python.timeutils as timeutils



def add_rehearsal(user_id: int, day: str, start: str, duration: str, song: str = None) -> tuple[str, discord.Embed, discord.Embed, discord.ui.View, bool]:
    """
    Returns ping, blocking_message (Embed/None), summary_message (Embed), request_ping (bool)
    """
    creator = db.check_user(user_id)

    #TODO revoir cette requête car il y a trop de problèmes possibles avec (error handling, injection...
    try:
        song_info = db.get_song_info(song)
    except db.SongNotFoundError:
        raise ValueError(f"Morceau « {song} » non trouvé !")
    except Exception:
        raise discordutils.FailureError

    ndate = tools.parse_date(day)
    nstart = tools.parse_time(start)

    start_time = timeutils.punctual_constraint_to_epoch(ndate + nstart)
    duration = tools.parse_duration(duration)

    instruments = db.get_instruments_names()

    blocking, missing, present = list(), list(), list()

    view = None

    for j in range(5, len(song_info ) -1):

        instrument = instruments[j][0]
        musicians = song_info[j].split(" ")

        for musician in musicians:
            if musician and musician not in blocking and musician not in missing and musician not in present:

                try:
                    uuid = db.run("""SELECT uuid, username FROM User WHERE email = ?;""", (musician,))
                except:
                    uuid = None
                if uuid:
                    uuid, username = uuid[0]

                    try:
                        blocking_events = db.request_blocking_events(start_time, duration, uuid)
                    except:
                        blocking_events = None

                    if blocking_events:
                        blocking.append([username, instrument, blocking_events[0]])
                    else:
                        present.append([username, uuid, instrument, musician])

                else:
                    missing.append([tools.parse_mail(musician), instrument])
    blocking_message = None
    if blocking or missing:

        blocking_message = discordutils.warning_embed(title=f"Blocages rencontrés : {len(present)} ")
        if len(present) <= 1:
            blocking_message.title += "personne disponible"
        else:
            blocking_message.title += f"personnes disponibles"

        if missing:
            missing_message = str()
            for absent_musician in missing:
                missing_message += f"- {absent_musician[0]} ({absent_musician[1]})\n"
            blocking_message.add_field(name="Ces personnes ne sont pas présentes dans la base de données", value=missing_message)

        if blocking:
            blocking_text = str()
            for blocked_musician in blocking:
                blocking_text += f"- {blocked_musician[0]} ({blocked_musician[1]}) : "
                if type(blocked_musician[2][0]) == str:
                    blocking_text += blocked_musician[2][0]
                else:
                    blocking_text += "indisponibilité personnelle"
                blocking_text += "\n"

            blocking_message.add_field(name="Ces personnes ne sont pas disponibles sur ce créneau", value=blocking_text)

        if len(present) > 1:
            view = discordutils.ConfirmView()
        else:
            view = discordutils.ConfirmViewImpossible()
        # await i.response.send_message(embed=message, view=view)
        # await view.wait()
        # if not view.value:
        #     await i.delete_original_response()
        #     return
    success = db.add_rehearsal_to_calendar(song, [i[3] for i in present], creator, timeutils.datetime_to_gcal(ndate+nstart), timeutils.datetime_to_gcal(ndate+timeutils.add_duration_to_time(nstart, duration)))

    summary_message = discordutils.success_embed(title="Répétition ajoutée", message=f"Répétition pour {song} {tools.get_special_date_string(ndate)} à **{tools.formatted_hhmm(nstart)}** d’une durée de **{tools.duration_to_string(duration)}** ajoutée avec succès.")
    
    present_message = str()
    ping = str()

    for present_musician in present:
        ping += f"<@{present_musician[1]}> "
        present_message += f"- {present_musician[0]} ({present_musician[2]})\n"

    summary_message.add_field(name="Membres présents", value=present_message)

    return ping, blocking_message, summary_message, view, blocking or missing, success


def find_rehearsal(song: str, start_time: int = None, length: int = 7*timeutils.DAY_DURATION) -> discord.Embed:
    evening_time = 22*3600
    try:
        # Fetch musicians' emails
        song_info = db.get_song_info(song)
        musicians_uuids = []
        unregistered_users = []
        for field in song_info[4:-1]:
            for email in field.split(" "):
                if len(email) > 17: # TODO valid email
                    value = db.run("""SELECT uuid FROM User WHERE email = ?;""", (email,))
                    if len(value) > 0:
                        musicians_uuids.append(value[0][0])
                    else:
                        unregistered_users.append(email)
        # Get the current time
        start_time = int((time.time()//3600+1)*3600) if start_time is None else start_time

        if start_time%timeutils.DAY_DURATION >= evening_time:
            start_time = int((start_time//timeutils.DAY_DURATION + 1)*timeutils.DAY_DURATION + 8*3600) # The next day at 8 AM
        current_week = timeutils.get_nbweeks(start_time)
        rehearsal_time = start_time
        rehearsals = [[] for i in range(7)]
        while timeutils.get_nbweeks(rehearsal_time) <= current_week:
            day_of_week = time.gmtime(rehearsal_time).tm_wday
            for musician_uuid in musicians_uuids:
                if len(db.request_blocking_events(rehearsal_time, 3600, musician_uuid)) == 0:
                    rehearsals[day_of_week].append(rehearsal_time)
                else:
                    print(f"""{time.strftime("%d/%m %H:%M", time.gmtime(rehearsal_time))} ({rehearsal_time%timeutils.DAY_DURATION}) : Impossible : {db.request_blocking_events(rehearsal_time, 3600, musician_uuid)}""")
                    event_start_time = db.request_blocking_events(rehearsal_time, 3600, musician_uuid)[0][1]
                    event_end_time = db.request_blocking_events(rehearsal_time, 3600, musician_uuid)[0][2]
                    timestamp = rehearsal_time
                    duration = 3600
                    # print(f"""({event_start_time} < {timestamp} AND {timestamp} < {event_end_time})""")
                    # print(f"""OR ({event_start_time} < {timestamp + duration} AND {timestamp + duration} < {event_end_time})""")
                    # print(f"""OR ({timestamp} <= {event_start_time} AND {event_end_time} <= {timestamp + duration})""")
                    # print(f"""OR ({event_start_time} < {tools.DAY_DURATION} AND (TRUE""")
                    # print(f"""  OR ({event_start_time} < {timestamp%tools.DAY_DURATION} AND {timestamp%tools.DAY_DURATION} < {event_end_time})""")
                    # print(f"""  OR ({event_start_time} < {timestamp%tools.DAY_DURATION + duration} AND {timestamp%tools.DAY_DURATION + duration} < {event_end_time})""")
                    # print(f"""  OR ({timestamp%tools.DAY_DURATION} <= {event_start_time} AND {event_end_time} <= {timestamp%tools.DAY_DURATION + duration})))""")
            rehearsal_time += 3600

        text = f"""Recherche à partir de {time.strftime("%d/%m %H:%M", time.gmtime(start_time))}\nRésultats:\n"""

        for index in range(len(rehearsals)):
            text += f"-----{index}-----\n"
            for val in rehearsals[index]:
                text += f"""{time.strftime("%d/%m %H:%M", time.gmtime(val))}\n"""

        return discordutils.information_embed(message=text)

    except Exception:
        raise discordutils.FailureError


def info(user_id: int, display: int) -> discord.Embed:
    title = f"Infos pour {db.check_user(user_id)}"
    try:
        desc = db.get_songs_message(user_id, display)
        return discordutils.information_embed(title=title, message=desc)
    except Exception:
        raise discordutils.FailureError


def song(song: str) -> discord.Embed:
    # TODO Je croyais que ça ne fonctionnait pas le unpacking implicite de liste/tuple ? Ça a été testé ?
    try:
        title, message = db.get_song_info_message(song)
        return discordutils.information_embed(title=title, message=message)
    except Exception:
        raise discordutils.FailureError