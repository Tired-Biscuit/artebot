# bot.py
import os
import time
import traceback
import math

import discord
from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands

import python.tools as tools
import python.db as db
import python.discordutils as discordutils
import python.googleutils as googleutils
import python.timeutils as timeutils
import python.commands.user_commands as user_commands
import python.commands.constraints_commands as constraints_commands
import python.commands.musics_commands as music_commands
import python.commands.admin_commands as admin_commands

DEBUG = True # Toggle the dev or production bot

# db.reset()
# db.init()
# register_lines(lines)

# db.update_timetables()

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

groups = tools.get_groups()
calendars = {"Google":"Google", "School":"École", "Spreadsheets":"Setlist"}
tables = ["User", "Song", "MusicianConstraint", "GoogleEvent", "SchoolEvent"]

group_choices = [app_commands.Choice(name=group, value=groups[group]) for group in groups]
calendar_choices = [app_commands.Choice(name=calendars[calendar], value=calendar) for calendar in calendars.keys()]
table_choices = [app_commands.Choice(name=table, value=table) for table in tables]

@bot.event
async def on_ready():
    await bot.tree.sync()




#########################
#     User Commands     #
#########################

@bot.tree.command(name="connexion", description="S’ajouter à la base de données")
@app_commands.describe(
    mail="Ton adresse mail TN.net",
    group="Groupe scolaire auquel tu appartiens (laisser vide si extérieur)"
)
@app_commands.rename(group="groupe")
@app_commands.choices(group=group_choices)
async def connection(i: discord.Interaction, mail: str, group: app_commands.Choice[str] = None):
    try:
        await i.response.send_message(embed=user_commands.connection(i.user.id, mail, group.value if group else ""), ephemeral=True)

    except Exception as e:
        await i.response.send_message(embed=discordutils.failure_embed(message=str(e)), ephemeral=True)


@bot.tree.command(name="mail", description="Changer l’adresse mail associée à son compte")
@app_commands.describe(
    mail="La nouvelle adresse mail (TN.net)"
)
async def mail(i: discord.Interaction, mail: str):
    try:
        await i.response.send_message(embed=user_commands.change_mail(i.user.id, mail), ephemeral=True)

    except Exception as e:
        await i.response.send_message(embed=discordutils.failure_embed(message=str(e)), ephemeral=True)


@bot.tree.command(name="groupe", description="Changer le groupe associé à son compte")
@app_commands.describe(
    group="Le nouveau groupe (laisser vide si extérieur)"
)
@app_commands.rename(group="groupe")
@app_commands.choices(group=group_choices)
async def group(i: discord.Interaction, group: app_commands.Choice[str] = None):
    try:
        await i.response.send_message(embed=user_commands.change_group(i.user.id, group.value if group else ""), ephemeral=True)

    except Exception as e:
        await i.response.send_message(embed=discordutils.failure_embed(message=str(e)), ephemeral=True)


@bot.tree.command(name="pseudo", description="Changer le pseudo associé à son compte")
@app_commands.describe(
    username="Ton nouveau pseudo (Prénom NOM par défaut)"
)
@app_commands.rename(username="pseudo")
async def username(i: discord.Interaction, username: str):
    try:
        await i.response.send_message(embed=user_commands.change_username(i.user.id, username), ephemeral=True)

    except Exception as e:
        await i.response.send_message(embed=discordutils.failure_embed(message=str(e)), ephemeral=True)



@bot.tree.command(name="profil", description="consulter le profil d’une personne. Laisse vide pour consulter ton profil")
@app_commands.describe(
    user="Mentionner la personne désirée (elle ne recevra pas de notification)"
)
@app_commands.rename(
    user="membre"
)
async def profile(i: discord.Interaction, user: discord.User=None):
    try:
        await i.response.send_message(embed=user_commands.profile(i.user.id if user is None else user.id), ephemeral=True)
    except Exception as e:
        await i.response.send_message(embed=discordutils.failure_embed(str(e)), ephemeral=True)




###############################
#     Constraint Commands     #
###############################

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
async def punctual_constraint(i: discord.Interaction, day: str, start: str = None, end: str = None):
    try:
        await i.response.send_message(embed=constraints_commands.punctual_constraint(i.user.id, day, start, end), ephemeral=True)

    except Exception as e:
        await i.response.send_message(embed=discordutils.failure_embed(message=str(e)), ephemeral=True)


@bot.tree.command(name="indisponibilité_récurrente", description="Ajouter une contrainte récurrente")
@app_commands.describe(
    day="Jour de la semaine de l’indisponibilité (peut être « Tous »)",
    start="Heure de début de l’indisponibilité",
    end="Heure de fin de l’indisponibilité"
)
@app_commands.choices(day=[
    app_commands.Choice(name="lundi", value=1),
    app_commands.Choice(name="mardi", value=2),
    app_commands.Choice(name="mercredi", value=3),
    app_commands.Choice(name="jeudi", value=4),
    app_commands.Choice(name="vendredi", value=5),
    app_commands.Choice(name="samedi", value=6),
    app_commands.Choice(name="dimanche", value=7),
    app_commands.Choice(name="tous", value=8)
])
@app_commands.rename(
    day="jour",
    start="début",
    end="fin"
)
async def recurring_constraint(i: discord.Interaction, day: app_commands.Choice[int], start: str = None, end: str = None):
    try:
        await i.response.send_message(embed=constraints_commands.recurring_constraint(i.user.id, day, start, end), ephemeral=True)

    except Exception as e:
        await i.response.send_message(embed=discordutils.failure_embed(message=str(e)), ephemeral=True)


@bot.tree.command(name="supprimer_indisponibilité", description="Retirer une contrainte")
async def delete_constraint(i: discord.Interaction):
    try:
        view = constraints_commands.delete_constraint(i.user.id)
        await i.response.send_message(embed=view.embed_page(), view=view)
    except Exception as e:
        await i.response.send_message(embed=discordutils.failure_embed(message=str(e)), ephemeral=True)


@bot.tree.command(name="voir_indisponibilités", description="Consulter les contraintes")
async def see_constraints(i:discord.Interaction):
    try:
        constraints = db.request_constraints(i.user.id)
        try:
            view = discordutils.ConstraintsPaginationView(constraints)
            await i.response.send_message(embed=view.embed_page(), view=view)
        except:
            raise discordutils.FailureError
    except Exception as e:
        await i.response.send_message(embed=discordutils.failure_embed(message=str(e)), ephemeral=True)




###########################
#     Musics Commands     #
###########################

@bot.tree.command(name="ajouter_répète", description="Ajouter un nouveau créneau de répétition pour un morceau")
@app_commands.describe(
    day="Jour de la répétition",
    start="Heure de début de la répétition",
    duration="Durée de la répétition",
    song="Si tu ne te trouves pas dans un fil, nom du morceau concerné par la répétition"
)
@app_commands.rename(
    day="jour",
    start="début",
    duration="durée",
    song="morceau"
)
async def add_rehearsal(i:discord.Interaction, day: str, start: str, duration: str, song: str = None):
    try:
        if song is None:
            if str(i.channel.type) == "public_thread" or str(i.channel.type) == "private_thread":
                song = i.channel.name
            else:
                raise EnvironmentError("Tu ne te trouves pas dans un fil ! Spécifie le morceau concerné ou lance la commande dans un fil portant le nom du morceau.")

        result = music_commands.add_rehearsal(i.user.id, day, start, duration, song)

        ping, blocking_message, summary_message, view, request_ping, success = result[0], result[1], result[2], result[3], result[4], result[5]


        if request_ping:
            await i.response.send_message(embed=blocking_message, view=view)
            await view.wait()
            if not view.value:
                await i.delete_original_response()

        if view is None or view.value:
            if success:
                if request_ping:
                    await i.followup.send(content=ping, embed=summary_message)
                else:
                    await i.response.send_message(content=ping, embed=summary_message)
            else:
                raise Exception("Erreur lors de l’ajout de la répétition au calendrier")
        

    except Exception as e:
        message = discordutils.failure_embed(title="Erreur", message=str(e))
        try:
            await i.response.send_message(embed=message, ephemeral=True)
        except:
            await i.followup.send(embed=message)


@bot.tree.command(name="trouver_repète", description="Trouve les créneaux possibles pour répéter un morceau sur les 7 prochains jours")
@app_commands.describe(
    song="Nom du morceau (laisser vide si tu es dans le fil correspondant)"
)
@app_commands.rename(
    song="morceau"
)
async def find_rehearsal(i: discord.Interaction, song: str = None):
    try:
        if song is None:
            if str(i.channel.type) == "public_thread" or str(i.channel.type) == "private_thread":
                song = i.channel.name
            else:
                raise EnvironmentError("Tu ne te trouves pas dans un fil ! Spécifie le morceau concerné ou lance la commande dans un fil portant le nom du morceau.")

        if not db.run("""SELECT title FROM Song WHERE title LIKE ?;""", ("%"+song+"%",)):
            raise ValueError(f"Morceau {song} non trouvé")

        view = discordutils.WeekSelectionView(song)
        await i.response.send_message(embed=view.embed_page(), view=view)

    except Exception as e:
        await i.response.send_message(embed=discordutils.failure_embed(message=str(e)))


@bot.tree.command(name="info", description="consulter les morceaux d’une personne. Laisse vide pour consulter tes morceaux.")
@app_commands.describe(
    user="Mentionner la personne désirée (elle ne recevra pas de notification)",
    display="Niveau d’information"
)
@app_commands.rename(
    user="membre",
    display="affichage"
)
@app_commands.choices(display=[
    app_commands.Choice(name="simplifié", value=0),
    app_commands.Choice(name="avancé", value=1),
    app_commands.Choice(name="complet", value=2)
])
async def info(i: discord.Interaction, user: discord.User=None, display: int = 2):
    try:
        embed = music_commands.info(i.user.id if user is None else user.id, display)
        if len(embed.description) > 4096:
            nb = math.ceil(len(embed.description)/4096)
            nembed = discordutils.information_embed(title=embed.title, message=embed.description[:4096])
            await i.response.send_message(embed=nembed, ephemeral=True)
            for j in range(nb-1):
                if 4096*(j+2) > len(embed.description):
                    nembed = discordutils.information_embed(title=embed.title, message=embed.description[4096*(j+1):])
                else:
                    nembed = discordutils.information_embed(title=embed.title, message=embed.description[4096*(j+2):])
                await i.followup.send(embed=nembed, ephemeral=True)
        else:    
            await i.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        await i.response.send_message(embed=discordutils.failure_embed(message=str(e)), ephemeral=True)


@bot.tree.command(name="morceau", description="obtenir des informations concernant un morceau en particulier.")
@app_commands.describe(
    song="Nom du morceau (peut être vide si tu te trouves dans un fil portant le nom du morceau !)"
)
@app_commands.rename(
    song="morceau"
)
async def song(i: discord.Interaction, song: str=None):
    try:
        if song is None:
            if str(i.channel.type) == "public_thread" or str(i.channel.type) == "private_thread":
                song = i.channel.name
            else:
                raise EnvironmentError("Tu ne te trouves pas dans un fil ! Spécifie le morceau concerné ou lance la commande dans un fil portant le nom du morceau.")

        
        song = db.run("""SELECT title FROM Song WHERE title LIKE ?;""", ("%"+song+"%",))

        if not song:
            raise ValueError(f"Morceau {song} non trouvé")
        
        song = song[0][0]

        await i.response.send_message(embed=music_commands.song(song), ephemeral=True)

    except Exception as e:
        await i.response.send_message(embed=discordutils.failure_embed(message=str(e)), ephemeral=True)




##########################
#     Admin Commands     #
##########################
#TODO Ajouter les décorateurs admin-only

@bot.tree.command(name="ajouter_admin", description="enregistrer quelqu’un comme admin")
@app_commands.describe(
    user="Mentionner la personne concernée"
)
@app_commands.rename(
    user="membre"
)
@discord.app_commands.guild_only()
@discord.app_commands.default_permissions(administrator=True)
async def add_admin(i: discord.Interaction, user: discord.User):
    try:
        await i.response.send_message(embed=admin_commands.add_admin(i.user.id, user.id), ephemeral=True)
    except Exception as e:
        await i.response.send_message(embed=discordutils.failure_embed(message=str(e)), ephemeral=True)


@bot.tree.command(name="couleur_intégrations", description="changer la couleur des intégrations Discord")
@app_commands.describe(
    colour="Nouvelle couleur (format hexadécimal XXXXXX)"
)
@app_commands.rename(
    colour="couleur"
)
@discord.app_commands.guild_only()
@discord.app_commands.default_permissions(administrator=True)
async def change_embed_colour(i: discord.Interaction, colour: str):
    try:
        await i.response.send_message(embed=admin_commands.change_embed_colour(i.user.id, colour), ephemeral=True)
    except Exception as e:
        await i.response.send_message(embed=discordutils.failure_embed(message=str(e)), ephemeral=True)


@bot.tree.command(name="actualiser", description="Met à jour un calendrier")
@app_commands.describe(
    calendar="Indiquer la ressource à mettre à jour"
)
@app_commands.rename(
    calendar="calendrier"
)
@app_commands.choices(calendar=calendar_choices)
@discord.app_commands.guild_only()
@discord.app_commands.default_permissions(administrator=True)
async def refresh(i: discord.Interaction, calendar: app_commands.Choice[str]):

    await i.response.defer()

    try:
        message = admin_commands.refresh(i.user.id, calendar.value)
    except Exception as e:
        message = discordutils.failure_embed(message=str(e))

    await i.followup.send(embed=message, ephemeral=True)


@bot.tree.command(name="ajouter_setlist", description="Ajoute une setlist")
@app_commands.describe(
    setlist_link="Lien de la setlist"
)
@app_commands.rename(
    setlist_link="lien"
)
@discord.app_commands.guild_only()
@discord.app_commands.default_permissions(administrator=True)
async def add_setlist(i: discord.Interaction, setlist_link: str):
    await i.response.defer()
    try:
        await i.followup.send(embed=admin_commands.add_setlist(i.user.id, setlist_link), ephemeral=True)
    except Exception as e:
        await i.followup.send(embed=discordutils.failure_embed(message=str(e)), ephemeral=True)


@bot.tree.command(name="supprimer_setlist", description="Retire une setlist")
@discord.app_commands.guild_only()
@discord.app_commands.default_permissions(administrator=True)
async def delete_setlist(i: discord.Interaction):
    try:
        db.check_user(i.user.id)
        if i.user.id not in tools.get_admins():
            raise discordutils.NotAdminError
        setlists_ids = tools.get_setlists_ids()
        view = discordutils.SetlistRemovalPaginationView(setlists_ids)
        await i.response.send_message(embed=view.embed_page(), view=view)
    except Exception as e:
        await i.response.send_message(embed=discordutils.failure_embed(message=str(e)), ephemeral=True)


@bot.tree.command(name="ajouter_calendrier", description="Ajouter un calendrier Google pour vérifier les contraintes")
@app_commands.describe(
    calendar_id="ID du calendrier"
)
@app_commands.rename(
    calendar_id="id"
)
@discord.app_commands.guild_only()
@discord.app_commands.default_permissions(administrator=True)
async def add_calendar(i: discord.Interaction, calendar_id: str):
    try:
        db.check_user(i.user.id)
        if i.user.id not in tools.get_admins():
            raise discordutils.NotAdminError
        tools.add_calendar(calendar_id)
        db.update_calendars()
        await i.response.send_message(embed=discordutils.success_embed("Ajout réussi"), ephemeral=True)
    except Exception as e:
        await i.response.send_message(embed=discordutils.failure_embed(message=str(e)), ephemeral=True)


@bot.tree.command(name="supprimer_calendrier", description="Retier un calendrier Google (dangereux)")
@app_commands.describe(
    calendar_id="ID du calendrier"
)
@app_commands.rename(
    calendar_id="id"
)
@discord.app_commands.guild_only()
@discord.app_commands.default_permissions(administrator=True)
async def remove_calendar(i: discord.Interaction, calendar_id: str):
    try:
        db.check_user(i.user.id)
        if i.user.id not in tools.get_admins():
            raise discordutils.NotAdminError
        tools.remove_calendar(calendar_id)
        db.update_calendars()
        await i.response.send_message(embed=discordutils.success_embed("Ajout réussi"), ephemeral=True)
    except Exception as e:
        await i.response.send_message(embed=discordutils.failure_embed(message=str(e)), ephemeral=True)


@bot.tree.command(name="créer_calendrier", description="Créer un calendrier Google lié à une setlist")
@discord.app_commands.guild_only()
@discord.app_commands.default_permissions(administrator=True)
async def create_calendar(i: discord.Interaction):
    try:
        db.check_user(i.user.id)
        if i.user.id not in tools.get_admins():
            raise discordutils.NotAdminError
        view = discordutils.SetlistChoiceForCalendarView(i.user.id, tools.get_setlists_ids())
        view.check_buttons_availability()
        await i.response.send_message(embed=view.embed_page(), view=view, ephemeral=True)
    except Exception as e:
        await i.response.send_message(embed=discordutils.failure_embed(message=str(e)), ephemeral=True)


@bot.tree.command(name="créer_fils", description="Créer un fil par morceau dans ce salon")
@discord.app_commands.guild_only()
@discord.app_commands.default_permissions(administrator=True)
async def create_threads(i: discord.Interaction):
    # Too complex to move to admin_commands
    try:
        db.check_user(i.user.id)
        if i.user.id not in tools.get_admins():
            raise discordutils.NotAdminError

        try:
            songs = db.run("SELECT * FROM Song")
        except:
            raise Exception("Problème avec les morceaux présents…")

        if str(i.channel.type) != "text":
            raise Exception("Tu ne trouves pas dans un salon !")

        existing_threads = [thread.name for thread in i.channel.threads]
        songs = [list(song) for song in songs if song[1] not in existing_threads]

        if not songs:
            await i.response.send_message(embed=discordutils.information_embed(message="Pas de fils à créer !"), ephemeral=True)
        else:
            await i.response.defer(thinking=False)
            setlists_names = googleutils.get_setlists_names()
            view = discordutils.SetlistsThreadCreationView(setlists_names)
            view.check_buttons_availability()
            await i.followup.send(embed=view.embed_page(), view=view)



    except Exception as e:
        try:
            await i.response.send_message(embed=discordutils.failure_embed(message=str(e)), ephemeral=True)
        except:
            await i.followup.send(embed=discordutils.failure_embed(message=str(e)), ephemeral=True)


@bot.tree.command(name="ajouter_instrument", description="Ajouter un instrument dans la BDD")
@discord.app_commands.guild_only()
@discord.app_commands.default_permissions(administrator=True)
@app_commands.describe(
    instrument="Nom de l’instrument en anglais",
    translation="Nom de l’instrument en français"
)
@app_commands.rename(
    instrument="instrument_anglais",
    translation="instrument_francais"
)
async def add_instrument(i: discord.Interaction, instrument: str, translation: str):
    try:
        db.add_instrument(instrument, translation)
        await i.response.send_message(embed=discordutils.success_embed(), ephemeral=True)
    except Exception as e:
        await i.response.send_message(embed=discordutils.failure_embed(message=str(e)), ephemeral=True)


@bot.tree.command(name="supprimer_table", description="Vider toutes les entrées d’une table de la base de données")
@app_commands.describe(
    table="Indiquer la table à vider"
)
@app_commands.rename(
    table="table"
)
@app_commands.choices(table=table_choices)
@discord.app_commands.guild_only()
@discord.app_commands.default_permissions(administrator=True)
async def delete_table(i: discord.Interaction, table: app_commands.Choice[str]):
    try:
        await i.response.send_message(embed=admin_commands.delete_table(i.user.id, table.value), ephemeral=True)
    except Exception as e:
        await i.response.send_message(embed=discordutils.failure_embed(message=str(e)), ephemeral=True)


#TODO voir_owners




##################################################################
#     Owner Commands (in python/commands/admin_commands.py)      #
##################################################################

@bot.tree.command(name="retirer_admin", description="(owner-only) retirer les droits d’admin du bot à quelqu’un")
@app_commands.describe(
    user="Mentionner la personne concernée"
)
@app_commands.rename(
    user="membre"
)
@discord.app_commands.guild_only()
@discord.app_commands.default_permissions(administrator=True)
async def remove_admin(i: discord.Interaction, user: discord.User):
    try:
        await i.response.send_message(embed=admin_commands.remove_admin(i.user.id, user.id), ephemeral=True)
    except Exception as e:
        await i.response.send_message(embed=discordutils.failure_embed(message=str(e)), ephemeral=True)


@bot.tree.command(name="ajouter_owner", description="(owner-only) enregistrer quelqu’un comme owner")
@app_commands.describe(
    user="Mentionner la personne concernée"
)
@app_commands.rename(
    user="membre"
)
@discord.app_commands.guild_only()
@discord.app_commands.default_permissions(administrator=True)
async def add_owner(i: discord.Interaction, user: discord.User):
    #TODO demander la confirmation
    if i.user.id in tools.get_owners():
        try:
            tools.add_admin(user.id)
            tools.add_owner(user.id)
            await i.response.send_message(embed=discordutils.success_embed(), ephemeral=True)
        except Exception as e:
            await i.response.send_message(embed=discordutils.failure_embed(message=str(e)), ephemeral=True)
    else:
        await i.response.send_message(embed=discordutils.failure_embed(message=str(discordutils.NotOwnerError)), ephemeral=True)


@bot.tree.command(name="réinit_db", description="(owner-only) réinitialise la base de données")
@discord.app_commands.guild_only()
@discord.app_commands.default_permissions(administrator=True)
#TODO ajouter un écran de confirmation
async def reset_database(i: discord.Interaction):
    try:
        await  i.response.send_message(embed=admin_commands.reinit_db(i.user.id), ephemeral=True)
    except Exception as e:
        await i.response.send_message(embed=discordutils.failure_embed(message=str(e)), ephemeral=True)




################
#     Test     #
################

@bot.tree.command(name="test", description="Some test about rehearsal selection")
async def test(i: discord.Interaction, song: str):
    try:
        view = discordutils.WeekSelectionView(song)
        await i.response.send_message(embed=view.embed_page(), view=view, ephemeral=True)
    except Exception as e:
        await i.response.send_message(embed=discordutils.failure_embed(message=str(e)), ephemeral=True)




#########################
#    End Of Content     #
#########################

@bot.tree.command(name="order_66", description="Execute order 66")
@discord.app_commands.guild_only()
@discord.app_commands.default_permissions(administrator=True)
async def order_66(i: discord.Interaction):
    await i.response.send_message(embed=discord.Embed(title="Trooper!", description="Execute order 66.", colour=tools.get_embed_colour()), ephemeral=True)


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
        message = discord.Embed(title=title, description=text, colour=tools.get_embed_colour())
        await ctx.author.send(embed=message)

@bot.command()
async def logs(ctx):
    title = "Logs"
    text = f"- info"+"\n"+f"  - réussis : {logs_data['info']['successful']}"+"\n"+f"  - ratés : {logs_data['info']['failed']}"+"\n"+f"- update"+"\n"+f"  - réussis : {logs_data['update']['successful']}"+"\n"+f"  - ratés : {logs_data['update']['failed']}"+"\n"+f"- logs : {logs_data['logs']}"
    logs_data["logs"] += 1
    message = discord.Embed(title=title, description=text, colour=tools.get_embed_colour())
    await ctx.author.send(embed=message)


#################################
#     /!\ DO NOT DELETE /!\     #
#################################

bot.run(TOKEN)