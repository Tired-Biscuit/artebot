import discord

import python.db as db
import python.tools as tools
import python.discordutils as discordutils
import python.timeutils as timeutils
import python.googleutils as googleutils
import math

def add_admin(author_id: int, user_id: int) -> discord.Embed:
    if author_id in tools.get_admins():
        try:
            db.check_user(user_id)
            tools.add_admin(user_id)
            return discordutils.success_embed()
        except Exception:
            raise discordutils.FailureError
    else:
        raise discordutils.NotAdminError


#TODO déplacer add_owner ici


def change_embed_colour(user_id: int, colour: str) -> discord.Embed:
    if user_id in tools.get_admins():
        try:
            tools.change_embed_colour(colour)
            return discordutils.success_embed()
        except Exception:
            raise discordutils.FailureError
    else:
        raise discordutils.NotAdminError


def refresh(user_id: int, source: str) -> discord.Embed:
    db.check_user(user_id)
    if user_id not in tools.get_admins():
        raise discordutils.NotAdminError
    if source == "Spreadsheets":
        for setlist_id in tools.get_setlists_ids():
            db.run("""DELETE FROM Song WHERE setlist_id = ?;""", (setlist_id,))
            db.add_setlist(setlist_id, 200)

        return discordutils.success_embed(message="Setlist mise à jour")
    elif source == "School":
        groups = tools.get_groups()
        for group_id in groups.values():
            db.run("""DELETE FROM SchoolEvent WHERE group_id = ?;""", (group_id,))
        errors = tools.download_timetables()
        db.update_timetables()
        if errors != "":
            raise Exception(errors)
        return discordutils.success_embed(message="Emplois du temps scolaire mis à jour")
    elif source == "Google":
        calendars = tools.get_calendars_ids()
        for calendar_id in calendars:
            db.run("""DELETE FROM GoogleEvent WHERE calendar_id = ?;""", (calendar_id,))
        db.update_calendars()

        return discordutils.success_embed(message="Agendas Google mis à jour")
    else:
        return discordutils.failure_embed(message=source)

def cleanup(user_id: int) -> discord.Embed:
    db.check_user(user_id)
    if user_id not in tools.get_admins():
        raise discordutils.NotAdminError

    try:
        db.cleanup()
        return discordutils.information_embed(message="Nettoyage réussi")
    except Exception as e:
        raise e
        raise discordutils.FailureError

def see_owners(user_id: int) -> discord.Embed:
    db.check_user(user_id)
    if user_id not in tools.get_admins():
        raise discordutils.NotAdminError
    result = ""
    data = db.get_owners()

    if data:
        for owner in data:
            result += f"{owner[0]} {owner[1]}\n"
    else:
        result = "Aucun owner trouvé!"
    return discordutils.information_embed(title="Owners", message=result)


def see_users(user_id: int) -> discord.Embed:
    db.check_user(user_id)
    if user_id not in tools.get_admins():
        raise discordutils.NotAdminError
    result = ""
    data = db.get_users()
    for user in data:
        result += f"{user[0]} {user[1]} {user[2]} {user[3]}\n"

    return discordutils.information_embed(title="Utilisateurs", message=result)


def add_setlist(user_id: int, setlist_link: str) -> discord.Embed:
    db.check_user(user_id)
    if user_id not in tools.get_admins():
        raise discordutils.NotAdminError
    if setlist_link != "":
        id = googleutils.get_spreadsheet_id(setlist_link)
        tools.add_setlist(id, googleutils.get_sheet_name(id))
        return discordutils.success_embed(message="Setlist ajoutée, pense à la mettre à jour!")
    else:
        raise discordutils.FailureError

#TODO déplacer remove setlist ici ?

def create_calendar(user_id: int, setlist_id: str) -> discord.Embed:
    db.check_user(user_id)
    if user_id not in tools.get_admins():
        raise discordutils.NotAdminError
    if setlist_id is not None:
        try:
            result = googleutils.create_setlist_calendar(setlist_id)
        except googleutils.ExistingCalendarError as e:
            raise e
        if result:
            return discordutils.success_embed(message=googleutils.get_calendar_share_link(setlist_id))
        else:
            raise discordutils.FailureError
    else:
        raise discordutils.FailureError

def delete_table(user_id: int, table: str) -> discord.Embed:
    if table.value == "User":
        db.check_user(user_id)
        if user_id not in tools.get_owners():
            return discordutils.failure_embed(title="Opération impossible", message="Il faut être owner pour supprimer les utilisateurs")
    if user_id not in tools.get_admins():
        raise discordutils.NotAdminError
    else:
        db.run(f"""DELETE FROM {table};""")
        return discordutils.success_embed(message=f"Entrées de la table {table} supprimées")


##########################
#     Owner Commands     #
##########################

def remove_admin(author_id: int, user_id: int) -> discord.Embed:
    if author_id in tools.get_owners():
        if author_id == user_id:
            return discordutils.warning_embed(message="Tu ne peux pas te retirer les droits")
        else:
            try:
                db.check_user(user_id)
                tools.remove_admin(user_id)
                return discordutils.success_embed()
            except Exception:
                raise discordutils.FailureError
    else:
        raise discordutils.NotOwnerError


def reinit_db(user_id: int) -> discord.Embed:
    db.check_user(user_id)
    if user_id in tools.get_owners():
        db.reset()
        db.init()
        return discordutils.success_embed()
    else:
        raise discordutils.NotOwnerError