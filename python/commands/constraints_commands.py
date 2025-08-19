import discord

import python.db as db
import python.tools as tools
import python.discordutils as discordutils
import python.timeutils as timeutils


def punctual_constraint(user_id: int, day: str, start: str = None, end: str = None) -> discord.Embed:

    username = db.check_user(user_id)

    if username:
        ndate = tools.parse_date(day)

        nstart = tools.parse_time(start) if start else "0000"

        nend = tools.parse_time(end) if end else "2359"

        start_unix = timeutils.punctual_constraint_to_epoch(ndate + nstart + "00")
        end_unix = timeutils.punctual_constraint_to_epoch(ndate + nend + "00")

        try:
            constraint = db.run(f"""SELECT * FROM MusicianConstraint WHERE musician_uuid = {user_id} AND start_time = "{start_unix}" AND end_time = "{end_unix}";""")
        except:
            raise discordutils.FailureError

        if not constraint:
            try:
                db.add_punctual_constraint(user_id, start_unix, end_unix)
            except:
                raise discordutils.FailureError
        else:
            raise ValueError("Cette contrainte existe déjà !")

        return discordutils.success_embed(title="Contrainte ajoutée", message=f"Indisponibilité pour {username} {tools.get_special_date_string(ndate)} {tools.formatted_time_span_string(nstart, nend)} ajoutée avec succès.")

    return discordutils.failure_embed()

def recurring_constraint(user_id: int, day: discord.app_commands.Choice, start: str = None, end: str = None) -> discord.Embed:
    username = db.check_user(user_id)

    if username:
        nstart = tools.parse_time(start) if start else "0000"
        nend = tools.parse_time(end) if end else "2359"

        start_epoch = int(nstart[:2]) * 3600 + int(nstart[2:]) * 60
        end_epoch = int(nend[:2]) * 3600 + int(nend[2:]) * 60

        try:
            constraint = db.run(f"""SELECT * FROM MusicianConstraint WHERE musician_uuid = {user_id} AND start_time = {start_epoch} AND end_time = {end_epoch} AND week_day = {day.value};""")
        except:
            raise discordutils.FailureError

        if not constraint:
            try:
                db.add_recurring_constraint(user_id, start_epoch, end_epoch, day.value)
            except:
                raise discordutils.FailureError
        else:
            raise ValueError("Cette contrainte existe déjà !")

        if day.value == 8:
            day_string = "jours"
        else:
            day_string = day.name.lower() + "s"

        return discordutils.success_embed(title="Contrainte ajoutée", message=f"Indisponibilité pour {username} tous les **{day_string}** {tools.formatted_time_span_string(nstart, nend)} ajoutée avec succès.")
    return discordutils.failure_embed()


def delete_constraint(user_id: int) -> discordutils.ConstraintRemovalPaginationView:
    db.check_user(user_id)

    try:
        constraints = db.request_constraints(user_id)
    except:
        raise discordutils.FailureError

    constraints_texts = []
    for constraint in constraints:
        if constraint[2] == 0:
            constraints_texts.append(tools.get_date_string(constraint[0]) + " " + tools.time_span_to_string(constraint[0], constraint[1]).replace("*", ""))
        else:
            if constraint[2] != 7:
                constraints_texts.append("Tous les " + timeutils.week_index_to_week_day(constraint[2]) + "s " + tools.time_span_to_string(constraint[0], constraint[1]).replace("*", ""))
            else:
                constraints_texts.append("Tous les jours " + tools.time_span_to_string(constraint[0], constraint[1]).replace("*", ""))

    view = discordutils.ConstraintRemovalPaginationView(constraints_texts, constraints, user_id)
    view.check_buttons_availability()
    return view

