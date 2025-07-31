import time

import discord
from discord import ButtonStyle

import python.tools as tools
import python.db as db

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
        return discord.Embed(title="Titre", description=self.pages[self.page])


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
        return tools.get_constraint_message(self.constraints, tools.get_first_day_of_week(tools.get_nbweeks(int(time.time())) + self.page))


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

    @discord.ui.button(label="Annuler", style=ButtonStyle.grey, custom_id="cancel")
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.prev_button.disabled = True
        self.next_button.disabled = True
        self.cancel_button.disabled = True
        self.delete_button.disabled = True
        await interaction.response.edit_message(embed=discord.Embed(title="Opération annulée"), view=self)

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
        return discord.Embed(title="Choisissez une setlist à supprimer", description=text)


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
        self.prev_button.disabled = True
        self.next_button.disabled = True
        self.cancel_button.disabled = True
        self.delete_button.disabled = True
        self.remove_constraint()
        await interaction.response.edit_message(embed=discord.Embed(title="Contrainte supprimée"), view=self)

    @discord.ui.button(label="Annuler", style=ButtonStyle.grey, custom_id="cancel")
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.prev_button.disabled = True
        self.next_button.disabled = True
        self.cancel_button.disabled = True
        self.delete_button.disabled = True
        await interaction.response.edit_message(embed=discord.Embed(title="Opération annulée"), view=self)

    def check_buttons_availability(self):
        self.prev_button.disabled = self.page <= 0
        self.next_button.disabled  = self.page >= len(self.constraints_strings) - 1

    def embed_page(self) -> discord.Embed:
        if len(self.constraints_strings) == 0:
            return discord.Embed(title="Aucune contrainte ajoutée")
        text = ""
        for i in range(len(self.constraints_strings)):
            if i == self.page:
                text += "**"
            text += self.constraints_strings[i]
            if i == self.page:
                text += "**"
            text += "\n"
        return discord.Embed(title="Choisissez une contrainte à supprimer", description=text)

    def remove_constraint(self):
        constraint = self.constraints[self.page]
        db.remove_constraint(self.musician_uuid, constraint[0], constraint[1], constraint[2])