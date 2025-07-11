import time

import discord
from discord import ButtonStyle

import python.tools as tools
from python.tools import get_nbweeks


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
        return tools.get_constraint_message(self.constraints, tools.get_first_day_of_week(get_nbweeks(int(time.time())) + self.page))