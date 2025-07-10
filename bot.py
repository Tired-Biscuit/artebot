# bot.py
import os
import time
import discord
from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands
import python.tools as tools
from python.tools import DELTA_TIME, UPDATE_TIME
import json
from discord.ui import View, Button
import python.db as db

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

group_choices = [app_commands.Choice(name=group, value=groups[group]) for group in groups]

@bot.event
async def on_ready():
    await bot.tree.sync()

@bot.tree.command(description="Test command with choices")
@app_commands.choices(name=[
    app_commands.Choice(name="name 1", value="value 1"),
    app_commands.Choice(name="name 2", value="value 2"),
    app_commands.Choice(name="name 3", value="value 3"),
])
async def test(i: discord.Interaction, name: app_commands.Choice[str]):
    message = discord.Embed(title="hello " + name.name)
    await i.response.send_message(embed=message)


@bot.tree.command(name="connexion", description="S'ajouter à la base de données")
@app_commands.describe(
    group="Groupe scolaire auquel tu appartiens",
    mail="Ton adresse mail TN.net"
)
@app_commands.rename(group="groupe")
@app_commands.choices(group=group_choices)

async def connection(i: discord.Interaction, group: app_commands.Choice[str], mail:str):
    try:
        # Check if user is already in the database
        if db.run(f"SELECT email FROM User WHERE uuid = '{i.user.id}'"):
            raise ValueError("tu es déjà dans la base de données !")

        pseudo = tools.parse_mail(mail)
        # Add user to the database
        db.add_user(str(i.user.id), pseudo, mail, group.value)

        message = discord.Embed(title="Ajout réussi", description=f"{pseudo} a été ajouté à la base de données avec succès. Tu peux changer ton pseudo avec la commande `/pseudo` !")
        await i.response.send_message(embed=message)

    except Exception as e:
        message = discord.Embed(title="Erreur", description=f"Une erreur est survenue lors de l'ajout : {str(e)}")
        await i.response.send_message(embed=message)


@bot.tree.command(name="mail", description="Changer l'adresse mail associée à son compte")
@app_commands.describe(
    mail="La nouvelle adresse mail (TN.net)"
)

async def mail(i: discord.Interaction, mail:str):
    try:
        if not db.run(f"SELECT email FROM User WHERE uuid = '{i.user.id}'"):
            raise ValueError()
        
        db.run(f"UPDATE User SET email = '{mail}' WHERE uuid = '{i.user.id}'")
        await i.response.send_message("Adresse mail modifiée avec succès !")
        
    except:
        await i.response.send_message("Erreur lors du changement de l'adresse mail, fais-tu partie de la base de données ? (`/connexion`)")

@bot.tree.command(name="pseudo", description="Changer le pseudo associé à son compte")
@app_commands.describe(
    pseudo="Ton nouveau pseudo (Prénom NOM par défaut)"
)

async def pseudo(i: discord.Interaction, pseudo:str):
    try:
        if not db.run(f"SELECT email FROM User WHERE uuid = '{i.user.id}'"):
            raise ValueError()

        db.run(f"UPDATE User SET username = '{pseudo}' WHERE uuid = '{i.user.id}'")
        await i.response.send_message("Pseudo modifié avec succès !")

    except:
        await i.response.send_message("Erreur lors du changement de pseudo, fais-tu partie de la base de données ? (`/connexion`)")


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
        await i.response.send_message(embed=message)

    except Exception as e:
        message = discord.Embed(title="Erreur", description=f"Une erreur est survenue lors de l'ajout de la contrainte : {str(e)}")
        await i.response.send_message(embed=message)


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
        await i.response.send_message(embed=message)

    except Exception as e:
        message = discord.Embed(title="Erreur", description=f"Une erreur est survenue lors de l'ajout de la contrainte : {str(e)}")
        await i.response.send_message(embed=message)


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
            if i.channel.type == "public_thread" or i.channel.type == "private_thread":
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

        instruments = db.get_instrument_names()

        blocks, absent, present = list(), list(), list()

        for j in range(3, len(song_info)):

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
            
            message = discord.Embed(title="Blocages rencontrés")

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

            view = ConfirmView()
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
            await i.response.send_message(embed=message)
        except:
            await i.followup.send(embed=message)


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
            title = f"Mise à jour impossible ⌛ temps restant: {int((DELTA_TIME - (time.time() - UPDATE_TIME))//3600)} heures {int((DELTA_TIME - (time.time() - UPDATE_TIME))%3600//60)} minutes et {int((DELTA_TIME - (time.time() - UPDATE_TIME))%3600%60)} secondes"
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