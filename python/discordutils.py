import time
from tty import setraw

import discord
from discord import ButtonStyle

import python.tools as tools
import python.timeutils as timeutils
import python.db as db

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


class SetlistsPaginationView(discord.ui.View):
    def __init__(self, setlists: list[str]):
        super().__init__()
        self.page = 0
        self.setlists = setlists

    @discord.ui.button(label="^", style=ButtonStyle.blurple, custom_id="prev", disabled=True)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
            self.check_buttons_availability()
            await interaction.response.edit_message(embed=self.embed_page(), view=self)

    @discord.ui.button(label="v", style=ButtonStyle.blurple, custom_id="next")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # if self.page < len(self.pages) - 1:
        self.page += 1
        self.check_buttons_availability()
        await interaction.response.edit_message(embed=self.embed_page(), view=self)

    @discord.ui.button(label="Supprimer", style=ButtonStyle.red, custom_id="delete")
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.prev_button.disabled = True
        self.next_button.disabled = True
        self.cancel_button.disabled = True
        self.delete_button.disabled = True
        tools.remove_setlist(self.page)
        await interaction.response.edit_message(embed=discord.Embed(title="Setlist supprimée"), view=self)

    @discord.ui.button(label="Terminer", style=ButtonStyle.grey, custom_id="end")
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.prev_button.disabled = True
        self.next_button.disabled = True
        self.cancel_button.disabled = True
        self.delete_button.disabled = True
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
        return information_embed(title="Choisissez une setlist à supprimer", message=text)


class ConstraintRemovalPaginationView(discord.ui.View):
    def __init__(self, constraints_strings: list[str], constraints: list[list[int]], musician_uuid: int):
        super().__init__()
        self.page = 0
        self.constraints_strings = constraints_strings
        self.constraints = constraints
        self.musician_uuid = musician_uuid

    @discord.ui.button(label="^", style=ButtonStyle.blurple, custom_id="prev", disabled=True)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
            self.check_buttons_availability()
            await interaction.response.edit_message(embed=self.embed_page(), view=self)

    @discord.ui.button(label="v", style=ButtonStyle.blurple, custom_id="next")
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
        return information_embed(title="Choisissez une contrainte à supprimer", message=text)

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
    def __init__(self, week: int = None):
        super().__init__()
        self.current_week = timeutils.get_nbweeks(int(time.time()))
        self.week = self.current_week if week is None else week

    def embed_page(self, message="") -> discord.Embed:
        return information_embed(title=f"Choisis la semaine: curr: {self.current_week}, sel: {self.week}", message=message)

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
        view = WeekDaySelectionView(self.week)
        await interaction.response.edit_message(embed=view.embed_page(), view=view)

    @discord.ui.button(label="Annuler", style=ButtonStyle.red, custom_id="cancel")
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.prev_button.disabled = True
        self.next_button.disabled = True
        self.confirm_button.disabled = True
        self.cancel_button.disabled = True
        await interaction.response.edit_message(embed=information_embed(title="Recherche annulée"), view=self)


class WeekDaySelectionView(discord.ui.View):
    def __init__(self, week: int = 0):
        super().__init__()
        self.week = week

    def embed_page(self, message="") -> discord.Embed:
        return information_embed(title="Jour", message=message)

    @discord.ui.button(label=timeutils.week_index_to_week_day(1), style=ButtonStyle.blurple, custom_id="monday", disabled=timeutils.is_week_index_before_today(1))
    async def monday_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view=RehearsalTimeSelectionView(week=self.week, weekdaynb=1)
        await interaction.response.edit_message(embed=view.embed_page(), view=view)

    @discord.ui.button(label=timeutils.week_index_to_week_day(2), style=ButtonStyle.blurple, custom_id="tuesday", disabled=timeutils.is_week_index_before_today(2))
    async def tuesday_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = RehearsalTimeSelectionView(week=self.week, weekdaynb=2)
        await interaction.response.edit_message(embed=view.embed_page(), view=view)

    @discord.ui.button(label=timeutils.week_index_to_week_day(3), style=ButtonStyle.blurple, custom_id="wednesday", disabled=timeutils.is_week_index_before_today(3))
    async def wednesday_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = RehearsalTimeSelectionView(week=self.week, weekdaynb=3)
        await interaction.response.edit_message(embed=view.embed_page(), view=view)

    @discord.ui.button(label=timeutils.week_index_to_week_day(4), style=ButtonStyle.blurple, custom_id="thursday", disabled=timeutils.is_week_index_before_today(4))
    async def thursday_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = RehearsalTimeSelectionView(week=self.week, weekdaynb=4)
        await interaction.response.edit_message(embed=view.embed_page(), view=view)

    @discord.ui.button(label=timeutils.week_index_to_week_day(5), style=ButtonStyle.blurple, custom_id="friday", disabled=timeutils.is_week_index_before_today(5))
    async def friday_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = RehearsalTimeSelectionView(week=self.week, weekdaynb=5)
        await interaction.response.edit_message(embed=view.embed_page(), view=view)

    @discord.ui.button(label=timeutils.week_index_to_week_day(6), style=ButtonStyle.blurple, custom_id="saturday", disabled=timeutils.is_week_index_before_today(6))
    async def saturday_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = RehearsalTimeSelectionView(week=self.week, weekdaynb=6)
        await interaction.response.edit_message(embed=view.embed_page(), view=view)

    @discord.ui.button(label="Retour", style=ButtonStyle.red, custom_id="back")
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = WeekSelectionView(self.week)
        await interaction.response.edit_message(embed=view.embed_page(), view=view)


class RehearsalTimeSelectionView(discord.ui.View):
    def __init__(self, week: int = 0, weekdaynb: int = 1):
        super().__init__()
        self.week = week
        self.weekdaynb = weekdaynb
        self.time = 0

    def embed_page(self, message="") -> discord.Embed:
        return information_embed(title="Choisis l'horaire", message=message)

    def update_buttons(self):
        limit = 15  # TODO nombre de créneaux dans une journée
        if self.time <= 0:
            self.time = limit + self.time
        elif self.time >= limit:
            self.time = self.time - limit

    @discord.ui.button(label="^", style=ButtonStyle.blurple, custom_id="prev")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.time -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embed_page(button.custom_id), view=self)

    @discord.ui.button(label="v", style=ButtonStyle.blurple, custom_id="next")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.time += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embed_page(button.custom_id), view=self)

    @discord.ui.button(label="Valider", style=ButtonStyle.green, custom_id="confirm")
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=self.embed_page(str(self.time)), view=self)

    @discord.ui.button(label="Retour", style=ButtonStyle.red, custom_id="back")
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = WeekDaySelectionView(self.week)
        await interaction.response.edit_message(embed=view.embed_page(), view=view)


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
NotAdminError = Exception("Tu n'es pas admin :(")
NotOwnerError = Exception("Tu n'es pas owner, les admins peuvent voir les owners avec /voir_owners")