import discord

import python.tools as tools
import python.discordutils as discordutils
import python.db as db

class UserAlreadyConnectedError(Exception):
    def __init__(self):
        super().__init__("Tu es déjà dans la base de données ! (`/connexion`)")

def connection(user_id: int, mail: str, group: str) -> discord.Embed:
    # Check if user is already in the database
    try:
        if db.run("""SELECT email FROM User WHERE uuid = ?;""", (user_id,)):
            raise UserAlreadyConnectedError
        if db.run("""SELECT uuid FROM User WHERE email == ?;""", (mail,)):
            raise Exception("L'addresse mail est déjà prise, contactez un admin.")
    except UserAlreadyConnectedError:
        raise UserAlreadyConnectedError
    except:
        raise Exception("L’identifiant n’a pas pu être vérifié")

    try:
        pseudo = tools.parse_mail(mail)
    except:
        raise ValueError(f"« {mail} » n’est pas une adresse mail valide.")

    try:
        # Add user to the database
        db.add_user(user_id, pseudo, mail, group)
    except:
        raise discordutils.FailureError

    return discordutils.success_embed(title="Ajout réussi", message=f"{pseudo} a été ajouté à la base de données avec succès. Tu peux changer ton pseudo avec la commande `/pseudo` !")

def change_mail(user_id: int, mail: str) -> discord.Embed:

    try:
        tools.parse_mail(mail)
    except:
        raise ValueError("Format de l’adresse mail incorrect !")

    try:
        db.check_user(user_id)
        db.run("UPDATE User SET email = ? WHERE uuid = ?;", (mail, user_id))
    except db.UserNotFoundError:
        db.add_user(user_id, db.get_user_name_from_email(mail), mail, "")
    except:
        raise discordutils.FailureError

    return discordutils.success_embed(message="Adresse mail modifiée avec succès !")

def change_group(user_id: int, group: str):
    db.check_user(user_id)

    try:
        db.run("""UPDATE User SET group_id = ? WHERE uuid = ?;""", (group, user_id))
    except:
        raise discordutils.FailureError

    return discordutils.success_embed(message="Groupe modifié avec succès !")


def change_username(user_id: int, username: str):
    db.check_user(user_id)

    try:
        db.run("""UPDATE User SET username = ? WHERE uuid = ?;""", (username, user_id))
    except:
        raise discordutils.FailureError

    return discordutils.success_embed(message="Pseudo modifié avec succès !")


def profile(user_id: int) -> discord.Embed:
    title = f"Profil de {db.check_user(user_id)}"
    try:
        return discordutils.information_embed(title=title, message=db.get_profile_message(user_id))
    except Exception:
        raise discordutils.FailureError
