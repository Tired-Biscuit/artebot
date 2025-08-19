import discord

import python.db as db
import python.tools as tools
import python.discordutils as discordutils
import python.timeutils as timeutils
import python.googleutils as googleutils


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


def refresh(user_id: int, calendar: str) -> discord.Embed:
    #TODO à compléter
    db.check_user(user_id)
    if user_id not in tools.get_admins():
        raise discordutils.NotAdminError
    if calendar == "Spreadsheets":
        for setlist_id in tools.get_setlists_ids():
            db.run(f"""DELETE FROM Song WHERE setlist_id = "{setlist_id}";""")
            db.add_setlist(setlist_id, 50)

        return discordutils.success_embed(message="Setlist mise à jour")
    else:
        return discordutils.failure_embed(message=calendar)


def add_setlist(user_id: int, setlist_link: str) -> discord.Embed:
    db.check_user(user_id)
    if user_id not in tools.get_admins():
        raise discordutils.NotAdminError
    if setlist_link != "":
        tools.add_setlist(googleutils.get_spreadsheet_id(setlist_link))
        return discordutils.success_embed(message="Setlist ajoutée, pensez à la mettre à jour!")
    else:
        raise discordutils.FailureError

#TODO déplacer remove setlist ici ?


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