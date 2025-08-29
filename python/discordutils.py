import time

import discord
from discord import ButtonStyle
from datetime import datetime

import python.tools as tools
import python.timeutils as timeutils
import python.db as db
import python.commands.admin_commands as admin_commands
import python.googleutils as googleutils


########################
#     Custom Views     #
########################

class ConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.value = None

    @discord.ui.button(label="Ajouter tout de même", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await interaction.response.edit_message(view=None)
        self.stop()

    @discord.ui.button(label="Annuler", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        await interaction.response.edit_message(view=None)
        self.stop()


class ConfirmViewImpossible(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.value = None

    @discord.ui.button(label="Ajouter tout de même", style=discord.ButtonStyle.success, disabled=True)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(label="Annuler", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        await interaction.response.edit_message(view=None)
        self.stop()

class PaginationView(discord.ui.View):
    def __init__(self, pages):
        super().__init__()
        self.page = 0
        self.pages = pages

    @discord.ui.button(label="<", style=ButtonStyle.blurple, custom_id="prev", disabled=True)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
            self.check_buttons_availability()
            await interaction.response.edit_message(embed=self.embed_page(), view=self)

    @discord.ui.button(label=">", style=ButtonStyle.blurple, custom_id="next")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < len(self.pages) - 1:
            self.page += 1
            self.check_buttons_availability()
            await interaction.response.edit_message(embed=self.embed_page(), view=self)

    def check_buttons_availability(self):
        print("page:", self.page, "prev_button.disabled", self.page <= 0,
        "next_button.disabled", self.page >= len(self.pages) - 1)
        self.prev_button.disabled = self.page <= 0
        self.next_button.disabled  = self.page >= len(self.pages) - 1

    def embed_page(self):
        return information_embed(title="Titre", message=self.pages[self.page])


class ConstraintsPaginationView(discord.ui.View):
    def __init__(self, constraints: list[list[int]]):
        super().__init__()
        self.page = 0
        self.constraints = constraints

    @discord.ui.button(label="<", style=ButtonStyle.blurple, custom_id="prev", disabled=True)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
            self.check_buttons_availability()
            await interaction.response.edit_message(embed=self.embed_page(), view=self)

    @discord.ui.button(label=">", style=ButtonStyle.blurple, custom_id="next")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # if self.page < len(self.pages) - 1:
        self.page += 1
        self.check_buttons_availability()
        await interaction.response.edit_message(embed=self.embed_page(), view=self)

    def check_buttons_availability(self):
        self.prev_button.disabled = self.page <= 0
        # self.next_button.disabled  = self.page >= len(self.pages) -

    def embed_page(self) -> discord.Embed:
        return get_constraint_embed(self.constraints, timeutils.get_first_day_of_week(timeutils.get_nbweeks(int(time.time())) + self.page))


class SetlistRemovalPaginationView(discord.ui.View):
    def __init__(self, setlists_ids: list[str]):
        super().__init__()
        self.page = 0
        self.setlists_ids = setlists_ids
        self.setlists_names = []

        for setlist_id in self.setlists_ids:
            self.setlists_names.append(tools.get_setlist_name(setlist_id))

    @discord.ui.button(label="⬆", style=ButtonStyle.blurple, custom_id="prev", disabled=True)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
            await interaction.response.edit_message(embed=self.embed_page(), view=self)

    @discord.ui.button(label="⬇", style=ButtonStyle.blurple, custom_id="next")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # if self.page < len(self.pages) - 1:
        self.page += 1
        await interaction.response.edit_message(embed=self.embed_page(), view=self)

    @discord.ui.button(label="Supprimer", style=ButtonStyle.red, custom_id="delete")
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.prev_button.disabled = True
        self.next_button.disabled = True
        self.cancel_button.disabled = True
        self.delete_button.disabled = True
        try:
            tools.remove_setlist(self.page)
            calendar_id = tools.get_setlist_calendar_id(self.setlists_names[self.page])
            if calendar_id:
                googleutils.delete_calendar(calendar_id)
            await interaction.response.edit_message(embed=success_embed(message="Setlist supprimée"), view=self)
        except Exception as e:
            await interaction.response.edit_message(embed=failure_embed(message=str(e)), view=self)

    @discord.ui.button(label="Annuler", style=ButtonStyle.grey, custom_id="end")
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.prev_button.disabled = True
        self.next_button.disabled = True
        self.cancel_button.disabled = True
        self.delete_button.disabled = True
        await interaction.response.edit_message(embed=discord.Embed(title="Opération annulée"), view=self)

    def check_buttons_availability(self):
        self.prev_button.disabled = self.page <= 0
        self.next_button.disabled  = self.page >= len(self.setlists_names) - 1

    def embed_page(self) -> discord.Embed:
        if len(self.setlists_names) == 0:
            self.cancel_button.disabled = True
            self.delete_button.disabled = True
            return discord.Embed(title="Aucune setlist ajoutée")
        text = ""
        for i in range(len(self.setlists_names)):
            if i == self.page:
                text += "**"
            text += self.setlists_names[i]
            if i == self.page:
                text += "**"
            text += "\n"
        self.check_buttons_availability()
        return information_embed(title="Choisis une setlist à supprimer", message=text)


class SetlistChoiceForCalendarView(discord.ui.View):
    def __init__(self, user_id: int, setlists_ids: list[str]):
        super().__init__()
        self.page = 0
        self.user_id = user_id
        self.setlists_ids = setlists_ids
        self.setlists_names = []

        for setlist_id in self.setlists_ids:
            self.setlists_names.append(tools.get_setlist_name(setlist_id))

    @discord.ui.button(label="⬆", style=ButtonStyle.blurple, custom_id="prev", disabled=True)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
            await interaction.response.edit_message(embed=self.embed_page(), view=self)

    @discord.ui.button(label="⬇", style=ButtonStyle.blurple, custom_id="next")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # if self.page < len(self.pages) - 1:
        self.page += 1
        await interaction.response.edit_message(embed=self.embed_page(), view=self)

    @discord.ui.button(label="Sélectionner", style=ButtonStyle.green, custom_id="confirm")
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.prev_button.disabled = True
        self.next_button.disabled = True
        self.cancel_button.disabled = True
        self.confirm_button.disabled = True
        await interaction.response.defer()
        # try:
        embed = admin_commands.create_calendar(self.user_id, self.setlists_ids[self.page])
        await interaction.followup.send(embed=embed, view=self)
        # except Exception as e:
        #     await interaction.followup.send(embed=failure_embed(message=str(e)))

    @discord.ui.button(label="Terminer", style=ButtonStyle.grey, custom_id="end")
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.prev_button.disabled = True
        self.next_button.disabled = True
        self.cancel_button.disabled = True
        self.confirm_button.disabled = True
        await interaction.response.edit_message(embed=discord.Embed(title="Opération terminée"), view=self)

    def check_buttons_availability(self):
        self.prev_button.disabled = self.page <= 0
        self.next_button.disabled  = self.page >= len(self.setlists_names) - 1

    def embed_page(self) -> discord.Embed:
        if len(self.setlists_names) == 0:
            self.confirm_button.disabled = True
            self.cancel_button.disabled = True
            return discord.Embed(title="Aucune setlist ajoutée")
        text = ""
        for i in range(len(self.setlists_names)):
            if i == self.page:
                text += "**"
            text += self.setlists_names[i]
            if i == self.page:
                text += "**"
            text += "\n"
        self.check_buttons_availability()
        return information_embed(title="Choisis une setlist pour le calendrier", message=text)


class SetlistChoiceForCalendarLinkView(discord.ui.View):
    def __init__(self, user_id: int, setlists_ids: list[str]):
        super().__init__()
        self.page = 0
        self.user_id = user_id
        self.setlists_ids = setlists_ids
        self.setlists_names = []

        for setlist_id in self.setlists_ids:
            self.setlists_names.append(tools.get_setlist_name(setlist_id))

    @discord.ui.button(label="⬆", style=ButtonStyle.blurple, custom_id="prev", disabled=True)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
            await interaction.response.edit_message(embed=self.embed_page(), view=self)

    @discord.ui.button(label="⬇", style=ButtonStyle.blurple, custom_id="next")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # if self.page < len(self.pages) - 1:
        self.page += 1
        await interaction.response.edit_message(embed=self.embed_page(), view=self)

    @discord.ui.button(label="Sélectionner", style=ButtonStyle.green, custom_id="confirm")
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.prev_button.disabled = True
        self.next_button.disabled = True
        self.cancel_button.disabled = True
        self.confirm_button.disabled = True
        await interaction.response.defer()
        try:
            embed = success_embed(googleutils.get_calendar_share_link(self.setlists_ids[self.page]))
            await interaction.followup.send(embed=embed, view=self)
        except Exception as e:
            await interaction.followup.send(embed=failure_embed(message=str(e)))

    @discord.ui.button(label="Terminer", style=ButtonStyle.grey, custom_id="end")
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.prev_button.disabled = True
        self.next_button.disabled = True
        self.cancel_button.disabled = True
        self.confirm_button.disabled = True
        await interaction.response.edit_message(embed=discord.Embed(title="Opération terminée"), view=self)

    def check_buttons_availability(self):
        self.prev_button.disabled = self.page <= 0
        self.next_button.disabled  = self.page >= len(self.setlists_names) - 1

    def embed_page(self) -> discord.Embed:
        if len(self.setlists_names) == 0:
            self.confirm_button.disabled = True
            self.cancel_button.disabled = True
            return discord.Embed(title="Aucune setlist ajoutée")
        text = ""
        for i in range(len(self.setlists_names)):
            if i == self.page:
                text += "**"
            text += self.setlists_names[i]
            if i == self.page:
                text += "**"
            text += "\n"
        self.check_buttons_availability()
        return information_embed(title="Choisis une setlist pour le calendrier", message=text)


class SetlistChoiceForCalendarAdd(discord.ui.View):
    def __init__(self, user_id: int, setlists_ids: list[str], calendar_id: str):
        super().__init__()
        self.page = 0
        self.user_id = user_id
        self.setlists_ids = setlists_ids
        self.setlists_names = []
        self.calendar_id = calendar_id

        for setlist_id in self.setlists_ids:
            self.setlists_names.append(tools.get_setlist_name(setlist_id))

    @discord.ui.button(label="⬆", style=ButtonStyle.blurple, custom_id="prev", disabled=True)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
            await interaction.response.edit_message(embed=self.embed_page(), view=self)

    @discord.ui.button(label="⬇", style=ButtonStyle.blurple, custom_id="next")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # if self.page < len(self.pages) - 1:
        self.page += 1
        await interaction.response.edit_message(embed=self.embed_page(), view=self)

    @discord.ui.button(label="Sélectionner", style=ButtonStyle.green, custom_id="confirm")
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.prev_button.disabled = True
        self.next_button.disabled = True
        self.cancel_button.disabled = True
        self.confirm_button.disabled = True
        await interaction.response.defer()
        try:
            tools.add_calendar(self.calendar_id)
            tools.add_calendar_to_setlist(self.setlists_ids[self.page], self.calendar_id)
            await interaction.followup.send(embed=success_embed(), view=self)
        except Exception as e:
            await interaction.followup.send(embed=failure_embed(message=str(e)))

    @discord.ui.button(label="Terminer", style=ButtonStyle.grey, custom_id="end")
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.prev_button.disabled = True
        self.next_button.disabled = True
        self.cancel_button.disabled = True
        self.confirm_button.disabled = True
        await interaction.response.edit_message(embed=discord.Embed(title="Opération terminée"), view=self)

    def check_buttons_availability(self):
        self.prev_button.disabled = self.page <= 0
        self.next_button.disabled  = self.page >= len(self.setlists_names) - 1

    def embed_page(self) -> discord.Embed:
        if len(self.setlists_names) == 0:
            self.confirm_button.disabled = True
            self.cancel_button.disabled = True
            return discord.Embed(title="Aucune setlist ajoutée")
        text = ""
        for i in range(len(self.setlists_names)):
            if i == self.page:
                text += "**"
            text += self.setlists_names[i]
            if i == self.page:
                text += "**"
            text += "\n"
        self.check_buttons_availability()
        return information_embed(title="Choisis une setlist à lier au calendrier", message=text)


class SetlistsThreadCreationView(discord.ui.View):
    def __init__(self, setlists: list[str]):
        super().__init__()
        self.page = 0
        self.setlists = setlists

    @discord.ui.button(label="⬆", style=ButtonStyle.blurple, custom_id="prev", disabled=True)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
            self.check_buttons_availability()
            await interaction.response.edit_message(embed=self.embed_page(), view=self)

    @discord.ui.button(label="⬇", style=ButtonStyle.blurple, custom_id="next")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # if self.page < len(self.pages) - 1:
        self.page += 1
        self.check_buttons_availability()
        await interaction.response.edit_message(embed=self.embed_page(), view=self)

    @discord.ui.button(label="Choisir", style=ButtonStyle.green, custom_id="choose")
    async def choose_button(self, i: discord.Interaction, button: discord.ui.Button):
        self.prev_button.disabled = True
        self.next_button.disabled = True
        self.cancel_button.disabled = True
        self.choose_button.disabled = True

        songs = db.run("""SELECT * FROM Song WHERE setlist_id LIKE ?;""", ("%"+tools.get_setlists_ids()[self.page]+"%",))

        songs = [list(song) for song in songs if song[1] not in [thread.name for thread in i.channel.threads]]

        if not songs:
            await i.response.edit_message(embed=information_embed(title=f"Pas de fils à créer !", message=""), view=None)
            
        description = str()
        for song in songs:
            description += f"- {song[1]} ({song[2]})\n"
        description = description[:-1]

        view = ThreadCreationView()
        
        if len(songs) != 1:
            await i.response.edit_message(embed=information_embed(title=f"{len(songs)} fils manquants", message=description), view=view)
        else:
            await i.response.edit_message(embed=information_embed(title=f"{len(songs)} fils manquants", message=description), view=view)

        await view.wait()
        if not view.value:
            await i.delete_original_response()
        else:

            await i.edit_original_response(embed=information_embed(title=f"0/{len(songs)} fil créé…", message=description))

            created = 0
            for k in range(len(songs)):
                musicians, not_in_db = db.get_song_musicians(songs[k])
                if musicians:
                    thread = await i.channel.create_thread(
                        name=songs[k][1],
                        auto_archive_duration=10080,
                        reason="Fil pour répétition"
                    )
                    songs[k][1] = ":white_check_mark: " + songs[k][1]
                    created += 1
                else:
                    songs[k][1] = ":x: (pas de musiciens dans la DB) " + songs[k][1]


                description = str()
                for j in range(len(songs)):
                    if j == k+1:
                        description += f"- **{songs[j][1]} ({songs[j][2]})**\n"
                    else:
                        description += f"- {songs[j][1]} ({songs[j][2]})\n"

                description = description[:-1]

                if created > 1:
                    await i.edit_original_response(embed=information_embed(title=f"{created}/{len(songs)} fils créés…", message=description))
                else:
                    await i.edit_original_response(embed=information_embed(title=f"{created}/{len(songs)} fil créé…", message=description))

                text = str()
                for musician in musicians:
                    text += f"<@{musician}> "

                if musicians:
                    await thread.send(text)
                    if not_in_db:
                        text = f"\n Les personnes suivantes ne sont pas dans la base de données du bot ! Mentionnez-les et demandez leur de se connecter avec `/connexion` !\n"
                        for musician in not_in_db:
                            text += f"- {tools.parse_mail(musician)}\n"

                        await thread.send(text)

            if songs:
                if created > 1:
                    await i.followup.send(f"{created} fils créés avec succès !", ephemeral=True)
                else:
                    await i.followup.send(f"{created} fil créé avec succès !", ephemeral=True)

    @discord.ui.button(label="Terminer", style=ButtonStyle.grey, custom_id="end")
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.prev_button.disabled = True
        self.next_button.disabled = True
        self.cancel_button.disabled = True
        self.choose_button.disabled = True
        await interaction.response.edit_message(embed=discord.Embed(title="Opération terminée"), view=self)

    def check_buttons_availability(self):
        self.prev_button.disabled = self.page <= 0
        self.next_button.disabled  = self.page >= len(self.setlists) - 1

    def embed_page(self) -> discord.Embed:
        if len(self.setlists) == 0:
            return discord.Embed(title="Aucune setlist ajoutée")
        text = ""
        for i in range(len(self.setlists)):
            if i == self.page:
                text += "**"
            text += self.setlists[i]
            if i == self.page:
                text += "**"
            text += "\n"
        return information_embed(title="Choisis une setlist pour laquelle créer les fils", message=text)


class ConstraintRemovalPaginationView(discord.ui.View):
    def __init__(self, constraints_strings: list[str], constraints: list[list[int]], musician_uuid: int):
        super().__init__()
        self.page = 0
        self.constraints_strings = constraints_strings
        self.constraints = constraints
        self.musician_uuid = musician_uuid

    @discord.ui.button(label="⬆", style=ButtonStyle.blurple, custom_id="prev", disabled=True)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
            self.check_buttons_availability()
            await interaction.response.edit_message(embed=self.embed_page(), view=self)

    @discord.ui.button(label="⬇", style=ButtonStyle.blurple, custom_id="next")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # if self.page < len(self.pages) - 1:
        self.page += 1
        self.check_buttons_availability()
        await interaction.response.edit_message(embed=self.embed_page(), view=self)

    @discord.ui.button(label="Supprimer", style=ButtonStyle.red, custom_id="delete")
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.delete_button.disabled = len(self.constraints_strings) == 0
        self.remove_constraint()
        self.check_buttons_availability()
        await interaction.response.edit_message(embed=self.embed_page(), view=self)

    @discord.ui.button(label="Terminer", style=ButtonStyle.grey, custom_id="end")
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.prev_button.disabled = True
        self.next_button.disabled = True
        self.cancel_button.disabled = True
        self.delete_button.disabled = True
        await interaction.response.edit_message(embed=discord.Embed(title="Terminé"), view=self)

    def check_buttons_availability(self):
        self.prev_button.disabled = self.page <= 0
        self.next_button.disabled  = self.page >= len(self.constraints_strings) - 1
        if self.page == len(self.constraints_strings):
            self.page -= 1

    def embed_page(self) -> discord.Embed:
        if len(self.constraints_strings) == 0:
            return information_embed(title="Aucune contrainte ajoutée")
        text = ""
        for i in range(len(self.constraints_strings)):
            if i == self.page:
                text += "**"
            text += self.constraints_strings[i]
            if i == self.page:
                text += "**"
            text += "\n"
        return information_embed(title="Choisiss une contrainte à supprimer", message=text)

    def remove_constraint(self):
        constraint = self.constraints[self.page]
        db.remove_constraint(self.musician_uuid, constraint[0], constraint[1], constraint[2])
        self.constraints_strings.pop(self.page)
        self.constraints.pop(self.page)


class ThreadCreationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.value = None

    @discord.ui.button(label="Créer", style=discord.ButtonStyle.success)
    async def create(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await interaction.response.edit_message(view=None)
        self.stop()

    @discord.ui.button(label="Annuler", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        await interaction.response.edit_message(view=None)
        self.stop()


class WeekSelectionView(discord.ui.View):
    """
    View displaying a week's timetable, and allowing navigation between weeks.
    """
    def __init__(self, song: str, week: int = None):
        super().__init__()
        self.current_week = timeutils.get_nbweeks(int(time.time()))
        self.song = song
        self.week = self.current_week if week is None else week
    
    def embed_page(self, message="") -> discord.Embed:
        self.update_buttons()
        # Fetch constraints (recurring and punctual separately)
        result = db.get_week_constraints_for_rehearsal(self.song, timeutils.get_first_day_of_week(self.week))
        # Get the message from the constraints
        message = tools.week_timetable_string_from_constraints(result[0], result[1])
        return information_embed(title=f"Semaine du {tools.epoch_to_ddmm(timeutils.get_first_day_of_week(self.week))} au {tools.epoch_to_ddmm(timeutils.get_first_day_of_week(self.week) + 6 * timeutils.DAY_DURATION)}", message=message)

    def update_buttons(self):
        self.prev_button.disabled = self.week <= self.current_week

    @discord.ui.button(label="<", style=ButtonStyle.blurple, custom_id="prev", disabled = True)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.week -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embed_page(str(self.week)), view=self)

    @discord.ui.button(label=">", style=ButtonStyle.blurple, custom_id="next")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.week += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embed_page(str(self.week)), view=self)

    @discord.ui.button(label="Valider", style=ButtonStyle.green, custom_id="confirm")
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = WeekDaySelectionView(self.song, self.week)
        await interaction.response.edit_message(embed=view.embed_page(), view=view)

    @discord.ui.button(label="Annuler", style=ButtonStyle.red, custom_id="cancel")
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.prev_button.disabled = True
        self.next_button.disabled = True
        self.confirm_button.disabled = True
        self.cancel_button.disabled = True
        await interaction.response.edit_message(embed=information_embed(title="Recherche annulée"), view=self)


class WeekDaySelectionView(discord.ui.View):
    """
    View disaplying a week's timetable and allowing week day selection
    """
    def __init__(self, song: str, week: int = 0):
        super().__init__()
        self.song = song
        self.week = week

    def embed_page(self, message="") -> discord.Embed:
        # Fetches the constraints, builds a timetable message, and returns en embed displaying them properly
        result = db.get_week_constraints_for_rehearsal(self.song, timeutils.get_first_day_of_week(self.week))
        message = tools.week_timetable_string_from_constraints(result[0], result[1])
        self.update_buttons_state()
        return information_embed(title=f"Semaine du {tools.epoch_to_ddmm(timeutils.get_first_day_of_week(self.week))} au {tools.epoch_to_ddmm(timeutils.get_first_day_of_week(self.week) + 6 * timeutils.DAY_DURATION)}", message=message)

    def update_buttons_state(self):
        self.monday_button.disabled = timeutils.is_day_before_today(timeutils.get_first_day_of_week(self.week))
        self.tuesday_button.disabled = timeutils.is_day_before_today(timeutils.get_first_day_of_week(self.week) + timeutils.DAY_DURATION*(1))
        self.wednesday_button.disabled = timeutils.is_day_before_today(timeutils.get_first_day_of_week(self.week) + timeutils.DAY_DURATION*(2))
        self.thursday_button.disabled = timeutils.is_day_before_today(timeutils.get_first_day_of_week(self.week) + timeutils.DAY_DURATION*(3))
        self.friday_button.disabled = timeutils.is_day_before_today(timeutils.get_first_day_of_week(self.week) + timeutils.DAY_DURATION*(4))
        self.saturday_button.disabled = timeutils.is_day_before_today(timeutils.get_first_day_of_week(self.week) + timeutils.DAY_DURATION*(5))

    @discord.ui.button(label=timeutils.week_index_to_week_day(1), style=ButtonStyle.blurple, custom_id="monday", disabled=True)
    async def monday_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view=ConstraintsDetailsView(song=self.song, week=self.week, weekdaynb=1)
        await interaction.response.edit_message(embed=view.embed_page(), view=view)

    @discord.ui.button(label=timeutils.week_index_to_week_day(2), style=ButtonStyle.blurple, custom_id="tuesday", disabled=True)
    async def tuesday_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = ConstraintsDetailsView(song=self.song, week=self.week, weekdaynb=2)
        await interaction.response.edit_message(embed=view.embed_page(), view=view)

    @discord.ui.button(label=timeutils.week_index_to_week_day(3), style=ButtonStyle.blurple, custom_id="wednesday", disabled=True)
    async def wednesday_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = ConstraintsDetailsView(song=self.song, week=self.week, weekdaynb=3)
        await interaction.response.edit_message(embed=view.embed_page(), view=view)

    @discord.ui.button(label=timeutils.week_index_to_week_day(4), style=ButtonStyle.blurple, custom_id="thursday", disabled=True)
    async def thursday_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = ConstraintsDetailsView(song=self.song, week=self.week, weekdaynb=4)
        await interaction.response.edit_message(embed=view.embed_page(), view=view)

    @discord.ui.button(label=timeutils.week_index_to_week_day(5), style=ButtonStyle.blurple, custom_id="friday", disabled=True)
    async def friday_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = RehearsalTimeSelectionView(song=self.song, week=self.week, weekdaynb=5)
        await interaction.response.edit_message(embed=view.embed_page(), view=view)

    @discord.ui.button(label=timeutils.week_index_to_week_day(6), style=ButtonStyle.blurple, custom_id="saturday", disabled=True)
    async def saturday_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = ConstraintsDetailsView(song=self.song, week=self.week, weekdaynb=6)
        await interaction.response.edit_message(embed=view.embed_page(), view=view)

    @discord.ui.button(label="Retour", style=ButtonStyle.grey, custom_id="back")
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = WeekSelectionView(self.song, self.week)
        await interaction.response.edit_message(embed=view.embed_page(), view=view)

    @discord.ui.button(label="Annuler", style=ButtonStyle.red, custom_id="cancel")
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.monday_button.disabled = True
        self.tuesday_button.disabled = True
        self.wednesday_button.disabled = True
        self.thursday_button.disabled = True
        self.friday_button.disabled = True
        self.saturday_button.disabled = True
        self.back_button.disabled = True
        self.cancel_button.disabled = True
        await interaction.response.edit_message(embed=information_embed(title="Recherche annulée"), view=self)


class ConstraintsDetailsView(discord.ui.View):
    """
    View displaying all constraints by start time for a given day of a given week
    """
    def __init__(self, song: str, week: int = 0, weekdaynb: int = 1):
        super().__init__()
        self.song = song
        self.week = week
        self.weekdaynb = weekdaynb

    def embed_page(self, message="") -> discord.Embed:
        # Fetch the musicians
        result = db.get_all_musicians_uuids_for_song(self.song)

        musicians_uuids = result[0]
        unregistered_users = result[1]

        data = []

        # For each musician, get constraints and add them in a list if not already present
        for musician_uuid in musicians_uuids:
            result = db.request_blocking_events(timeutils.get_first_day_of_week(self.week) + (self.weekdaynb - 1)*timeutils.DAY_DURATION, timeutils.DAY_DURATION, musician_uuid)
            data = data + list(set(result) - set(data))

        data = sorted(data, key=lambda x: x[1])

        message = ""

        # Build the string, one line per event
        for event in data:
            char = None
            if event[3] == 1:
                # School event
                char = "🟦"
            elif event[3] == 2 and char is None:
                # Google event
                char = "🟨"
            elif event[3] == 3 and char is None:
                # Punctual Constraint
                char = "🟥"
            else:
                if char is None:
                    char = "🟪"
            message += f"""{char} {tools.time_span_to_string(event[1], event[2])} - {event[0] if event[3] != 3 else "Indisponible"}\n"""
        message += ""
        return information_embed(title=tools.get_date_string(timeutils.get_first_day_of_week(self.week) + (self.weekdaynb - 1)*timeutils.DAY_DURATION), message=message)

    @discord.ui.button(label="Suivant", style=ButtonStyle.green, custom_id="confirm")
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = RehearsalTimeSelectionView(self.song, self.week, self.weekdaynb)
        await interaction.response.edit_message(embed=view.embed_page(), view=view)

    @discord.ui.button(label="Retour", style=ButtonStyle.grey, custom_id="back")
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = WeekDaySelectionView(self.song, self.week)
        await interaction.response.edit_message(embed=view.embed_page(), view=view)

    @discord.ui.button(label="Annuler", style=ButtonStyle.red, custom_id="cancel")
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.prev_button.disabled = True
        self.next_button.disabled = True
        self.confirm_button.disabled = True
        self.back_button.disabled = True
        self.cancel_button.disabled = True
        await interaction.response.edit_message(embed=information_embed(title="Recherche annulée"), view=self)


class RehearsalTimeSelectionView(discord.ui.View):
    """
    View displaying a day timetable, allowing navigation through each time slot from 8:00AM to 10:000PM

    Displays the events happening during the selected time span, and allows creating a rehearsal poll if a time slot is available
    """
    def __init__(self, song: str, week: int = 0, weekdaynb: int = 1):
        super().__init__()
        self.song = song
        self.week = week
        self.weekdaynb = weekdaynb
        self.time = 0

    def embed_page(self, message="") -> discord.Embed:
        result = db.get_day_constraints_for_rehearsal(self.song, timeutils.get_first_day_of_week(self.week) + timeutils.DAY_DURATION*(self.weekdaynb - 1))
        result = tools.day_timetable_string_from_constraints(result[0], result[1], self.time)
        message = result[0]
        self.confirm_button.disabled = not result[1]
        self.update()
        return information_embed(title=tools.get_date_string(timeutils.get_first_day_of_week(self.week) + (self.weekdaynb - 1)*timeutils.DAY_DURATION), message=message)

    def update(self):
        limit = 15  # TODO nombre de créneaux dans une journée
        if self.time < 0:
            self.time = limit + self.time
        elif self.time >= limit:
            self.time = self.time - limit

    @discord.ui.button(label="<", style=ButtonStyle.blurple, custom_id="prev")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.time -= 1
        self.update()
        await interaction.response.edit_message(embed=self.embed_page(button.custom_id), view=self)

    @discord.ui.button(label=">", style=ButtonStyle.blurple, custom_id="next")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.time += 1
        self.update()
        await interaction.response.edit_message(embed=self.embed_page(button.custom_id), view=self)

    @discord.ui.button(label="Valider", style=ButtonStyle.green, custom_id="confirm", disabled=True)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):

        day_epoch = timeutils.get_first_day_of_week(self.week) + (self.weekdaynb - 1)*timeutils.DAY_DURATION
        starttime = day_epoch + (self.time + 7) * 3600
        endtime = day_epoch + (self.time + 8) * 3600

        try:
            success = googleutils.add_rehearsal_to_calendar(self.song, [], "", timeutils.epoch_to_gcal(starttime), timeutils.epoch_to_gcal(endtime))

            summary_message = success_embed(
                title="Répétition ajoutée",
                message=f"Répétition pour {self.song} le {tools.get_date_string(day_epoch)} à **{tools.formatted_hhmm(tools.parse_time(str(self.time + 8)))}** d’une durée d’**une heure** ajoutée avec succès."
            )
        
            ping = str()

            for present_musician in db.get_all_musicians_uuids_for_song(self.song)[0]:
                ping += f"<@{present_musician}> "

            await interaction.response.edit_message(content=ping, embed=summary_message, view=None)
        except googleutils.NoCalendarError:
            await interaction.response.edit_message(embed=failure_embed(message="Aucun calendrier n'est lié à la setlist, merci de rapporter cela à un admin :)"))
        except Exception as e:
            await interaction.response.edit_message(embed=failure_embed(message="La répétition n’a pas pu être ajoutée au calendrier !"), view=None)

    @discord.ui.button(label="Retour", style=ButtonStyle.grey, custom_id="back")
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = ConstraintsDetailsView(self.song, self.week, self.weekdaynb)
        await interaction.response.edit_message(embed=view.embed_page(), view=view)

    @discord.ui.button(label="Annuler", style=ButtonStyle.red, custom_id="cancel")
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.prev_button.disabled = True
        self.next_button.disabled = True
        self.confirm_button.disabled = True
        self.back_button.disabled = True
        self.cancel_button.disabled = True
        await interaction.response.edit_message(embed=information_embed(title="Recherche annulée"), view=self)


def get_constraint_embed(constraints: list[list[int]], start_time) -> discord.embeds.Embed:
    """
    Builds a Discord Embed to display constraints
    """
    message = information_embed(title=f"Semaine du {tools.epoch_to_ddmm(start_time)} au {tools.epoch_to_ddmm(timeutils.get_first_day_of_week(timeutils.get_nbweeks(start_time)) + 6 * timeutils.DAY_DURATION)}", message=tools.get_constraints_week_description(constraints, start_time))
    return message



##########################
#     Generic Embeds     #
##########################

def success_embed(title: str = "Opération réussie", message: str = "") -> discord.Embed:
    return discord.Embed(title=title, description=message, colour=tools.get_embed_colour())

def warning_embed(title: str = "Attention", message: str = "Un léger problème est survenu") -> discord.Embed:
    return discord.Embed(title=title, description=message, colour=tools.get_embed_colour())

def failure_embed(title: str = "Erreur", message: str = "Une erreur est survenue") -> discord.Embed:
    return discord.Embed(title=title, description=message, colour=tools.get_embed_colour())

def information_embed(title: str = "", message: str = "") -> discord.Embed:
    return discord.Embed(title=title, description=message, colour=tools.get_embed_colour())

############################################
#     Generic user-firendly Exceptions     #
############################################

FailureError = Exception("Une erreur est survenue")
NotAdminError = Exception("Tu n’es pas admin :(")
NotOwnerError = Exception("Tu n’es pas owner, les admins peuvent voir les owners avec /voir_owners")