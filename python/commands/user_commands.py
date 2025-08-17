import discord

import python.db as db
import python.tools as tools
import python.discordutils as discordutils

def connection(user_id: int, mail: str, group: str) -> discord.Embed:
    # Check if user is already in the database
    try:
        if db.run(f"""SELECT email FROM User WHERE uuid = {user_id};"""):
            raise ValueError("Tu es déjà dans la base de données ! (`/connexion`)")
    except:
        raise Exception("L'identifiant n'a pas pu être vérifié")

    try:
        pseudo = tools.parse_mail(mail)
    except:
        raise ValueError(f"« {mail} » n'est pas une adresse mail valide.")

    try:
        # Add user to the database
        db.add_user(str(user_id), pseudo, mail, group)
    except:
        raise discordutils.FailureError

    return discordutils.success_embed(title="Ajout réussi", message=f"{pseudo} a été ajouté à la base de données avec succès. Tu peux changer ton pseudo avec la commande `/pseudo` !")

def change_mail(user_id: int, mail: str) -> discord.Embed:
    db.check_user(user_id)

    try:
        tools.parse_mail(mail)
    except:
        raise ValueError("Format de l'adresse mail incorrect !")

    try:
        db.run(f"UPDATE User SET email = '{mail}' WHERE uuid = '{user_id}'")
    except:
        raise discordutils.FailureError

    return discordutils.success_embed(message="Adresse mail modifiée avec succès !")

def change_group(user_id: int, group: str):
    db.check_user(user_id)

    try:
        db.run(f"""UPDATE User SET group_id = "{group}" WHERE uuid = "{user_id}";""")
    except:
        raise discordutils.FailureError

    return discordutils.success_embed(message="Groupe modifié avec succès !")


def change_username(user_id: int, username: str):
    db.check_user(user_id)

    try:
        db.run(f"""UPDATE User SET username = "{username}" WHERE uuid = "{user_id}";""")
    except:
        raise discordutils.FailureError

    return discordutils.success_embed(message="Pseudo modifié avec succès !")


def profile(user_id: int) -> discord.Embed:
    title = f"Profil de {db.check_user(user_id)}"
    try:
        return discordutils.information_embed(title=title, message=db.get_profile_message(user_id))
    except Exception:
        raise discordutils.FailureError
