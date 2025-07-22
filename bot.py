# bot.py
import os
import time
import traceback

import discord
from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands, Interaction
import python.tools as tools
import json
from discord.ui import View, Button
import python.db as db
import python.discordutils as discordutils
import python.googleutils as googleutils

DEBUG = True # Toggle the dev or production bot

# db.reset()
# db.init()
# register_lines(lines)

# For metering purposes
logs_data = {"update": {"successful":0, "failed":0}, "info":{"successful":0, "failed":0}, "logs":0}

# Get tokens
load_dotenv()
if DEBUG:
    TOKEN = os.getenv('DEV_TOKEN')
else:
    TOKEN = os.getenv('DISCORD_TOKEN')

# Setup bot config
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Set command prefix
if DEBUG:
    bot = commands.Bot(command_prefix='/', intents=intents)
else:
    bot = commands.Bot(command_prefix='$', intents=intents)



# # # # # # # # # # # # # # #
#        New content        #
# # # # # # # # # # # # # # #

with open("groups.json", "r", encoding="utf-8") as f:
    groups = json.load(f)

calendars = {"Google":"Google", "School":"École", "Spreadsheets":"Setlist"}

group_choices = [app_commands.Choice(name=group, value=groups[group]) for group in groups]
calendar_choices = [app_commands.Choice(name=calendars[calendar], value=calendar) for calendar in calendars.keys()]

@bot.event
async def on_ready():
    await bot.tree.sync()

@bot.tree.command(name="connexion", description="S'ajouter à la base de données")
@app_commands.describe(
    group="Groupe scolaire auquel tu appartiens (laisser vide si extérieur)",
    mail="Ton adresse mail TN.net"
)
@app_commands.rename(group="groupe")
@app_commands.choices(group=group_choices)

async def connection(i: discord.Interaction, mail:str, group: app_commands.Choice[str] = None):
    try:
        # Check if user is already in the database
        if db.run(f"SELECT email FROM User WHERE uuid = '{i.user.id}'"):
            raise ValueError("tu es déjà dans la base de données !")

        pseudo = tools.parse_mail(mail)
        # Add user to the database
        db.add_user(str(i.user.id), pseudo, mail, group.value if group else "")

        message = discord.Embed(title="Ajout réussi", description=f"{pseudo} a été ajouté à la base de données avec succès. Tu peux changer ton pseudo avec la commande `/pseudo` !")
        await i.response.send_message(embed=message, ephemeral=True)

    except Exception as e:
        message = discord.Embed(title="Erreur", description=f"Une erreur est survenue lors de l'ajout : {str(e)}")
        await i.response.send_message(embed=message, ephemeral=True)


@bot.tree.command(name="mail", description="Changer l'adresse mail associée à son compte")
@app_commands.describe(
    mail="La nouvelle adresse mail (TN.net)"
)

async def mail(i: discord.Interaction, mail:str):
    try:
        if not db.run(f"SELECT email FROM User WHERE uuid = '{i.user.id}'"):
            raise ValueError()
        
        db.run(f"UPDATE User SET email = '{mail}' WHERE uuid = '{i.user.id}'")
        await i.response.send_message("Adresse mail modifiée avec succès !", ephemeral=True)
        
    except:
        await i.response.send_message("Erreur lors du changement de l'adresse mail, fais-tu partie de la base de données ? (`/connexion`)", ephemeral=True)

@bot.tree.command(name="groupe", description="Changer le groupe associé à son compte")
@app_commands.describe(
    group="Le nouveau groupe (laisser vide si extérieur)"
)
@app_commands.rename(group="groupe")
@app_commands.choices(group=group_choices)

async def group(i: discord.Interaction, group: app_commands.Choice[str] = None):
    try:
        if not db.run(f"SELECT email FROM User WHERE uuid = '{i.user.id}'"):
            raise ValueError()
        
        db.run(f"UPDATE User SET group_id = '{group.value if group else ''}' WHERE uuid = '{i.user.id}'")
        await i.response.send_message("Groupe modifié avec succès !", ephemeral=True)
        
    except:
        await i.response.send_message("Erreur lors du changement de groupe, fais-tu partie de la base de données ? (`/connexion`)", ephemeral=True)

@bot.tree.command(name="pseudo", description="Changer le pseudo associé à son compte")
@app_commands.describe(
    pseudo="Ton nouveau pseudo (Prénom NOM par défaut)"
)

async def pseudo(i: discord.Interaction, pseudo:str):
    try:
        if not db.run(f"SELECT email FROM User WHERE uuid = '{i.user.id}'"):
            raise ValueError()

        db.run(f"UPDATE User SET username = '{pseudo}' WHERE uuid = '{i.user.id}'")
        await i.response.send_message("Pseudo modifié avec succès !", ephemeral=True)

    except:
        await i.response.send_message("Erreur lors du changement de pseudo, fais-tu partie de la base de données ? (`/connexion`)", ephemeral=True)


@bot.tree.command(name="indisponibilité", description="Ajouter une contrainte ponctuelle")
@app_commands.describe(
    day="Jour de la contrainte",
    start="Heure de début de la contrainte (optionnel)",
    end="Heure de fin de la contrainte (optionnel)"
)
@app_commands.rename(
    day="jour",
    start="début",
    end="fin"
)

async def punctual_constraint(i:discord.Interaction, day: str, start: str = None, end: str = None):
    try:
        name = db.run(f"SELECT username FROM User WHERE uuid = '{i.user.id}'")
        if not name:
            raise ValueError(f"tu ne fais pas partie de la base de données ! Ajoute-toi avec `/connexion`.")

        name = name[0][0]

        ndate = tools.parse_date(day)

        nstart = tools.parse_time(start) if start else "0000"
        
        nend = tools.parse_time(end) if end else "2359"

        start_unix = tools.local_to_unixepoch(ndate + nstart)
        end_unix = tools.local_to_unixepoch(ndate + nend)
        
        if not db.run(f"SELECT * FROM MusicianConstraint WHERE musician_uuid = {i.user.id} AND start_time = '{start_unix}' AND end_time = '{end_unix}'"):
            db.add_punctual_constraint(i.user.id, start_unix, end_unix)
        else:
            raise ValueError("cette contrainte existe déjà !")

        message = discord.Embed(title="Contrainte ajoutée", description=f"Indisponibilité pour {name} {tools.date_to_string(ndate)} {tools.formatted_time_span_string(nstart, nend)} ajoutée avec succès.")
        await i.response.send_message(embed=message, ephemeral=True)

    except Exception as e:
        message = discord.Embed(title="Erreur", description=f"Une erreur est survenue lors de l'ajout de la contrainte : {str(e)}")
        await i.response.send_message(embed=message, ephemeral=True)


@bot.tree.command(name="indisponibilité_récurrente", description="Ajouter une contrainte récurrente")
@app_commands.describe(
    day="Jour de la semaine de l'indisponibilité (peut être « Tous »)",
    start="Heure de début de l'indisponibilité",
    end="Heure de fin de l'indisponibilité"
)
@app_commands.choices(day=[
    app_commands.Choice(name="Lundi", value=1),
    app_commands.Choice(name="Mardi", value=2),
    app_commands.Choice(name="Mercredi", value=3),
    app_commands.Choice(name="Jeudi", value=4),
    app_commands.Choice(name="Vendredi", value=5),
    app_commands.Choice(name="Samedi", value=6),
    app_commands.Choice(name="Dimanche", value=7),
    app_commands.Choice(name="Tous", value=8)
])
@app_commands.rename(
    day="jour",
    start="début",
    end="fin"
)

async def recurring_constraint(i:discord.Interaction, day: app_commands.Choice[int], start:str = None, end: str = None):
    try:
        name = db.run(f"SELECT username FROM User WHERE uuid = '{i.user.id}'")
        if not name:
            raise ValueError(f"tu ne fais pas partie de la base de données ! Ajoute-toi avec `/connexion`.")

        name = name[0][0]

        nstart = tools.parse_time(start) if start else "0000"
        nend = tools.parse_time(end) if end else "2359"

        start_unix = int(nstart[:2])*3600 + int(nstart[2:])*60
        end_unix = int(nend[:2])*3600 + int(nend[2:])*60

        if not db.run(f"SELECT * FROM MusicianConstraint WHERE musician_uuid = {i.user.id} AND start_time = '{start_unix}' AND end_time = '{end_unix}' AND week_day = {day.value}"):
            db.add_recurring_constraint(i.user.id, start_unix, end_unix, day.value)
        else:
            raise ValueError("cette contrainte existe déjà !")

        if day.value == 8:
            day_string = "jours"
        else:
            day_string = day.name.lower() + "s"

        message = discord.Embed(
            title="Contrainte ajoutée",
            description=f"Indisponibilité pour {name} tous les **{day_string}** {tools.formatted_time_span_string(nstart, nend)} ajoutée avec succès."
        )
        await i.response.send_message(embed=message, ephemeral=True)

    except Exception as e:
        message = discord.Embed(title="Erreur", description=f"Une erreur est survenue lors de l'ajout de la contrainte : {str(e)}")
        await i.response.send_message(embed=message, ephemeral=True)


class ConfirmView(View):
            def __init__(self):
                super().__init__(timeout=60)
                self.value = None

            @discord.ui.button(label="Ajouter tout de même", style=discord.ButtonStyle.success)
            async def confirm(self, interaction: discord.Interaction, button: Button):
                self.value = True
                await interaction.response.edit_message(view=None)
                self.stop()

            @discord.ui.button(label="Annuler", style=discord.ButtonStyle.danger)
            async def cancel(self, interaction: discord.Interaction, button: Button):
                self.value = False
                await interaction.response.edit_message(view=None)
                self.stop()

class ConfirmViewImpossible(View):
            def __init__(self):
                super().__init__(timeout=60)
                self.value = None

            @discord.ui.button(label="Ajouter tout de même", style=discord.ButtonStyle.success, disabled=True)
            async def confirm(self, interaction: discord.Interaction, button: Button):
                pass

            @discord.ui.button(label="Annuler", style=discord.ButtonStyle.danger)
            async def cancel(self, interaction: discord.Interaction, button: Button):
                self.value = False
                await interaction.response.edit_message(view=None)
                self.stop()

@bot.tree.command(name="ajouter_répète", description="Ajouter un nouveau créneau de répétition pour un morceau")
@app_commands.describe(
    day="Jour de la répétition",
    start="Heure de début de la répétition",
    duration="Durée de la répétition",
    song="Si vous ne vous trouvez pas dans un fil, nom du morceau concerné par la répétition"
)
@app_commands.rename(
    day="jour",
    start="début",
    duration="durée",
    song="morceau"
)
async def add_rehearsal(i:discord.Interaction, day:str, start:str, duration:str, song:str=None):
    try:
        if song is None:
            if str(i.channel.type) == "public_thread" or str(i.channel.type) == "private_thread":
                song = i.channel.name
            else:
                raise EnvironmentError("tu ne te trouves pas dans un fil ! Spécifie le morceau concerné ou lance la commande dans un fil portant le nom du morceau.")


        song_info = db.run(f"SELECT * FROM Song WHERE title LIKE '%{song}%'")

        if not song_info:
            raise ValueError(f"morceau {song} non trouvé !")

        song_info = song_info[0]

        ndate = tools.parse_date(day)
        nstart = tools.parse_time(start)

        start_time = tools.local_to_unixepoch(ndate + nstart)
        duration = tools.parse_duration(duration)

        instruments = db.get_instruments_names()

        blocks, absent, present = list(), list(), list()

        for j in range(4, len(song_info)-1):

            instrument = instruments[j]
            musicians = song_info[j].split(" ")

            for musician in musicians:
                if musician and musician not in blocks and musician not in absent and musician not in present:

                    uuid = db.run(f"SELECT uuid, username FROM User WHERE email = '{musician}'")
                    if uuid:
                        uuid, username = uuid[0]
                        blocking_events = db.request_blocking_events(start_time, duration, uuid)

                        if blocking_events:
                            blocks.append([username, instrument, blocking_events[0]])
                        else:
                            present.append([username, uuid, instrument])

                    else:
                        absent.append([tools.parse_mail(musician), instrument])

        if blocks or absent:

            message = discord.Embed(title=f"Blocages rencontrés : {len(present)} ")
            if len(present) <= 1:
                message.title += "personne disponible" 
            else:
                message.title += f"personnes disponibles"

            if absent:
                absents_message = str()
                for absent_musician in absent:
                    absents_message += f"- {absent_musician[0]} ({absent_musician[1]})\n"
                message.add_field(name="Ces personnes ne sont pas présentes dans la base de données", value=absents_message)

            if blocks:
                blocks_message = str()
                for blocked_musician in blocks:
                    blocks_message += f"- {blocked_musician[0]} ({blocked_musician[1]}) : "
                    if (type(blocked_musician[2][0]) == str):
                        blocks_message += blocked_musician[2][0]
                    else:
                        blocks_message += "indisponibilité personnelle"
                    blocks_message += "\n"

                message.add_field(name="Ces personnes ne sont pas disponibles sur ce créneau", value=blocks_message)

            if len(present) > 1:
                view = ConfirmView()
            else:
                view = ConfirmViewImpossible()
            await i.response.send_message(embed=message, view=view)
            await view.wait()
            if not view.value:
                await i.delete_original_response()
                return

        # TODO : add rehearsal to the calendar

        message = discord.Embed(
            title="Répétition ajoutée",
            description=f"Répétition pour {song} {tools.date_to_string(ndate)} à **{tools.formatted_hhmm(nstart)}** d'une durée de **{tools.duration_to_string(duration)}** ajoutée avec succès."
        )

        present_message = str()
        ping = str()

        for present_musician in present:
            ping += f"<@{present_musician[1]}> "
            present_message += f"- {present_musician[0]} ({present_musician[2]})\n"

        message.add_field(name="Membres présents", value=present_message)

        if blocks or absent:
            await i.followup.send(content=ping, embed=message)
        else:
            await i.response.send_message(content=ping, embed=message)

    except Exception as e:
        message = discord.Embed(title="Erreur", description=f"Une erreur est survenue lors de l'ajout de la répétition : {str(e)}")
        try:
            await i.response.send_message(embed=message, ephemeral=True)
        except:
            await i.followup.send(embed=message)


@bot.tree.command(name="voir_indisponibilités", description="Consulter les indisponibilités")

async def see_constraints(i:discord.Interaction):#, button: discord.ui.Button):
    try:
        constraints: list[list[int]] = db.run(f"""
            SELECT start_time, end_time, week_day FROM MusicianConstraint
            WHERE musician_uuid = '{i.user.id}'
            ORDER BY start_time ASC, week_day ASC;
        """)
        if not constraints:
            raise ValueError(f"Aucune donnée trouvée.")

        if len(constraints[0]) > 0:
            view = discordutils.ConstraintsPaginationView(constraints)
            await i.response.send_message(embed=view.embed_page(), view=view)
        else:
            raise Exception("Pas de contraintes trouvées.")

    except Exception as e:
        message = discord.Embed(title="Erreur", description=f"{str(e)}")
        await i.response.send_message(embed=message, ephemeral=True)

@bot.tree.command()
async def pages(i:discord.Interaction):
    pages = ["Un", "Deux", "Trois"]
    view = discordutils.PaginationView(pages)
    await i.response.send_message(embed=view.embed_page(), view=view)

@bot.tree.command(name="ajouter_admin", description="enregistrer un utilisateur comme admin")
@app_commands.describe(
    user="Mentionner la personne concernée"
)
@app_commands.rename(
    user="membre"
)

async def add_admin(i: discord.Interaction, user: discord.User):
    if i.user.id in tools.get_admins():
        try:
            tools.add_admin(user.id)
            await i.response.send_message(content="Opération effectuée", ephemeral=True)
        except Exception:
            await i.response.send_message(embed=discord.Embed(title="Une erreur est survenue", description=traceback.format_exc()), ephemeral=True)
    else:
        await i.response.send_message(content="Vous n'êtes pas admin :(", ephemeral=True)

@bot.tree.command(name="retirer_admin", description="(owner-only) retirer les droits d'admin du bot à quelqu'un")
@app_commands.describe(
    user="Mentionner la personne concernée"
)
@app_commands.rename(
    user="membre"
)

async def remove_admin(i: discord.Interaction, user: discord.User):
    if i.user.id in tools.get_owners():
        if i.user.id == user.id:
            await i.response.send_message(content="Vous ne pouvez pas vous retirer les droits", ephemeral=True)
        else:
            try:
                tools.remove_admin(user.id)
                await i.response.send_message(content="Opération effectuée", ephemeral=True)
            except Exception:
                await i.response.send_message(embed=discord.Embed(title="Une erreur est survenue", description=traceback.format_exc()), ephemeral=True)
    else:
        await i.response.send_message(content="Vous n'êtes pas owner :(", ephemeral=True)


@bot.tree.command(name="info", description="consulter les morceaux d'une personne. Laisser vide pour consulter vos morceaux.")
@app_commands.describe(
    user="Mentionner la personne désirée (elle ne recevra pas de notification)."
)
@app_commands.rename(
    user="membre"
)

async def info(i: discord.Interaction, user: discord.User=None):
    try:
        if user == None:
            uuid = i.user.id
        else:
            uuid = user.id
        title = f"Infos pour {db.get_user_name(uuid)}"
        message = discord.Embed(title=title, description=db.get_songs_message(uuid))
        await i.response.send_message(embed=message, ephemeral=True)
    except Exception as e:
        await i.response.send_message(embed=discord.Embed(title="Erreur", description=e), ephemeral=True)


@bot.tree.command(name="actualiser", description="Met à jour un calendrier")
@app_commands.describe(
    calendar="Indiquer la ressource à mettre à jour"
)
@app_commands.rename(
    calendar="calendrier"
)
@app_commands.choices(calendar=calendar_choices)

async def refresh(i: discord.Interaction, calendar: app_commands.Choice[str]):
    title = f"Mise à jour du calendrier {calendar.value}"
    if calendar.value == "Spreadsheets":
        db.run("DELETE FROM Song;")
        for setlist_id in tools.get_setlists_ids():
            db.add_setlist(setlist_id, 28)
        message=discord.Embed(title="Setlist mise à jour")
    else:
        message=discord.Embed(title=calendar.value)
    await i.response.send_message(embed=message, ephemeral=True)


@bot.tree.command(name="ajouter_setlist", description="Ajoute une setlist")
@app_commands.describe(
    setlist_link="Lien de la setlist"
)
@app_commands.rename(
    setlist_link="lien"
)

async def add_setlist(i: discord.Interaction, setlist_link: str):
    if setlist_link != "":
        try:
            tools.add_setlist(googleutils.get_spreadsheet_id(setlist_link))
            message = discord.Embed(title="Setlist ajoutée")
            await i.response.send_message(embed=message, ephemeral=True)
        except Exception:
            await i.response.send_message(embed=discord.Embed(title="Erreur", description=traceback.format_exc()), ephemeral=True)
    else:
        await i.response.send_message(embed=discord.Embed(title="Paramètre vide!"), ephemeral=True)


@bot.tree.command(name="supprimer_setlist", description="Supprime une setlist")

async def delete_setlist(i: discord.Interaction):
    setlists_names = googleutils.get_setlists_names()
    view = discordutils.SetlistsPaginationView(setlists_names)
    view.check_buttons_availability()
    await i.response.send_message(embed=view.embed_page(), view=view)


@bot.tree.command(name="reinit_db", description="(owner-only) réinitialise la base de données")
#TODO ajouter un écran de confirmation
async def reset_database(i: discord.Interaction):
    if i.user.id in tools.get_owners():
        try:
            db.reset()
            db.init()
            await i.response.send_message(content="Opération effectuée", ephemeral=True)
        except Exception:
            await i.response.send_message(embed=discord.Embed(title="Une erreur est survenue", description=traceback.format_exc()), ephemeral=True)
    else:
        await i.response.send_message(content="Vous n'êtes pas owner :(", ephemeral=True)


@bot.tree.command(name="order_66", description="Execute order 66")
@discord.app_commands.guild_only()
@discord.app_commands.default_permissions(administrator=True)
async def order_66(i: discord.Interaction):
    await i.response.send_message(embed=discord.Embed(title="Trooper!", description="Execute order 66."), ephemeral=True)

@bot.command()
async def foo(ctx):
    await ctx.send("miam")

# # # # # # # # # # # # # # #
#     Outdated content      #
# # # # # # # # # # # # # # #

@bot.command()
async def update(ctx, opt=""):
    text = ""
    try:
        if not db.update_db(opt=="force"):
            title = f"Mise à jour impossible ⌛ temps restant: {int((tools.DELTA_TIME - (time.time() - tools.UPDATE_TIME))//3600)} heures {int((tools.DELTA_TIME - (time.time() - tools.UPDATE_TIME))%3600//60)} minutes et {int((tools.DELTA_TIME - (time.time() - tools.UPDATE_TIME))%3600%60)} secondes"
            logs_data["update"]["failed"] += 1
        else:
            title = "Mise à jour réussie ✅"
            logs_data["update"]["successful"] += 1
    except Exception as e:
        print(e)
        text = str(e)
        title = "Mise à jour impossible ❌"
        logs_data["update"]["failed"] += 1
    finally:
        message = discord.Embed(title=title, description=text)
        await ctx.author.send(embed=message)

@bot.command()
async def logs(ctx):
    title = "Logs"
    text = f"- info"+"\n"+f"  - réussis : {logs_data['info']['successful']}"+"\n"+f"  - ratés : {logs_data['info']['failed']}"+"\n"+f"- update"+"\n"+f"  - réussis : {logs_data['update']['successful']}"+"\n"+f"  - ratés : {logs_data['update']['failed']}"+"\n"+f"- logs : {logs_data['logs']}"
    logs_data["logs"] += 1
    message = discord.Embed(title=title, description=text)
    await ctx.author.send(embed=message)

bot.run(TOKEN)