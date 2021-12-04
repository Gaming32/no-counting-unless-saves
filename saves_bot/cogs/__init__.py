from typing import TYPE_CHECKING

from discord.ext import commands

if TYPE_CHECKING:
    from saves_bot.bot import SavesBot


class BaseCog(commands.Cog):
    bot: 'SavesBot'

    def __init__(self, bot: 'SavesBot') -> None:
        self.bot = bot
