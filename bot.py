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
import python.db as db

DEBUG = True # Toggle the dev or production bot

# reset()
# init()
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
    groupe="Groupe scolaire auquel tu appartiens",
    mail="Ton adresse mail TN.net"
)
@app_commands.choices(groupe=group_choices)

async def connexion(i: discord.Interaction, groupe: app_commands.Choice[str], mail:str):
    try:
        # Check if user is already in the database
        if db.run(f"SELECT email FROM User WHERE uuid = '{i.user.id}'"):
            raise ValueError("tu es déjà dans la base de données !")

        pseudo = tools.parse_mail(mail)
        # Add user to the database
        db.add_user(i.user.id, pseudo, mail, groupe.value)

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
    jour="Jour de la contrainte",
    début="Heure de début de la contrainte (optionnel)",
    fin="Heure de fin de la contrainte (optionnel)"
)

async def indisponibilité(i:discord.Interaction, jour:str, début:str = None, fin:str = None):
    try:
        name = db.run(f"SELECT username FROM User WHERE uuid = '{i.user.id}'")
        if not name:
            raise ValueError(f"tu ne fais pas partie de la base de données ! Ajoute-toi avec `/connexion`.")

        name = name[0][0]

        ndate = tools.parse_date(jour)
        
        nstart = tools.parse_time(début) if début else "0000"
        
        nend = tools.parse_time(fin) if fin else "2359"

        start_unix = tools.local_to_unixepoch(ndate + nstart)
        end_unix = tools.local_to_unixepoch(ndate + nend)

        db.add_punctual_constraint(i.user.id, start_unix, end_unix)

        message = discord.Embed(title="Contrainte ajoutée", description=f"Indisponibilité pour {name} {tools.date_to_string(ndate)} {tools.time_span_to_string(nstart, nend)} ajoutée avec succès.")
        await i.response.send_message(embed=message)

    except Exception as e:
        message = discord.Embed(title="Erreur", description=f"Une erreur est survenue lors de l'ajout de la contrainte : {str(e)}")
        await i.response.send_message(embed=message)


@bot.tree.command(name="indisponibilité_récurrente", description="Ajouter une contrainte récurrente")
@app_commands.describe(
    jour="Jour de la semaine de l'indisponibilité (peut être « Tous »)",
    début="Heure de début de l'indisponibilité",
    fin="Heure de fin de l'indisponibilité"
)
@app_commands.choices(jour=[
    app_commands.Choice(name="Lundi", value=1),
    app_commands.Choice(name="Mardi", value=2),
    app_commands.Choice(name="Mercredi", value=3),
    app_commands.Choice(name="Jeudi", value=4),
    app_commands.Choice(name="Vendredi", value=5),
    app_commands.Choice(name="Samedi", value=6),
    app_commands.Choice(name="Dimanche", value=7),
    app_commands.Choice(name="Tous", value=8)
])

async def indisponibilité_récurrente(i:discord.Interaction, jour: app_commands.Choice[int], début:str = None, fin: str = None):
    try:
        name = db.run(f"SELECT username FROM User WHERE uuid = '{i.user.id}'")
        if not name:
            raise ValueError(f"tu ne fais pas partie de la base de données ! Ajoute-toi avec `/connexion`.")

        name = name[0][0]

        nstart = tools.parse_time(début) if début else "0000"
        nend = tools.parse_time(fin) if fin else "2359"

        start_unix = int(nstart[:2])*3600 + int(nstart[2:])*60
        end_unix = int(nend[:2])*3600 + int(nend[2:])*60

        db.add_recurring_constraint(i.user.id, start_unix, end_unix, jour.value)

        if jour.value == 8:
            day_string = "jours"
        else:
            day_string = jour.name.lower() + "s"

        message = discord.Embed(
            title="Contrainte ajoutée",
            description=f"Indisponibilité pour {name} tous les **{day_string}** {tools.time_span_to_string(nstart, nend)} ajoutée avec succès."
        )
        await i.response.send_message(embed=message)

    except Exception as e:
        message = discord.Embed(title="Erreur", description=f"Une erreur est survenue lors de l'ajout de la contrainte : {str(e)}")
        await i.response.send_message(embed=message)


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
