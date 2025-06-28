# bot.py
import os
import time
import discord
from dotenv import load_dotenv
from discord.ext import commands
import tools
from tools import DELTA_TIME, UPDATE_TIME
import db

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
    bot = commands.Bot(command_prefix='!', intents=intents)
else:
    bot = commands.Bot(command_prefix='$', intents=intents)


















@bot.command()
async def info(ctx, *, name=""):
    if name == "":
        message = discord.Embed(title="Erreur", description="Pas de prénom fourni!")
    else:
        try:
            text = db.get_songs(name)
            logs_data["info"]["successful"] += 1
        except:
            text = "Il y a eu une erreur, veuillez la signaler à Paul (@.tiredbiscuit)"
            logs_data["info"]["failed"] += 1
        message = discord.Embed(title="Résultats", description=(text if text != "  " else "Pas de résultats"))
    await ctx.author.send(embed=message)

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
