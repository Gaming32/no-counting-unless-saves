import asyncio
import logging
from typing import Optional

import discord
from discord.errors import HTTPException
from discord.ext import commands, tasks
from discord.flags import Intents
from multidict import MultiDict

from saves_bot.cogs.config import ConfigCog
from saves_bot.constants import COUNTING_BOT_ID
from saves_bot.data import SavesData


VALID_COMMANDS = {
    'server', 'user'
}

INTENTS = Intents.default()
INTENTS.members = True


class SavesBot(commands.Bot):
    data: SavesData
    waiting_commands: MultiDict[discord.Message]

    def __init__(self):
        super().__init__('::', intents=INTENTS)
        self.data = SavesData()
        self.waiting_commands = MultiDict()
        self.add_listener(self.on_ready)
        self.add_cog(ConfigCog(self))
        self.add_command(commands.Command(
            self.shutdown_command,
            name='shutdown',
            brief='Shuts down the bot',
        ))

    async def on_ready(self):
        logging.info('Preparing bot...')
        if not self.refresh_data.is_running():
            self.refresh_data.start()
        await self.change_presence(
            activity=discord.Activity(
                name=f'{self.command_prefix}help',
                type=discord.ActivityType.listening
            )
        )
        logging.info('%s ready!', self.user)

    async def close(self) -> None:
        self.refresh_data.cancel()
        await self.data.refresh_data()
        await super().close()

    @tasks.loop(minutes=10)
    async def refresh_data(self) -> None:
        await self.data.refresh_data()

    @commands.check(lambda ctx: ctx.author.id == 338005893377556480)
    async def shutdown_command(self, ctx: commands.Context) -> None:
        await ctx.send('Shutting down bot!')
        await self.close()

    def _get_embed_type(self, title: str) -> Optional[str]:
        l = len(title)
        if l >= 1 and title.startswith('Info for `') and title[-1] == '`':
            return 'server'
        elif l >= 5 and title[-5] == '#' and title[-4:].isnumeric():
            return 'user'

    async def on_message(self, message: discord.Message) -> None:
        await super().on_message(message)
        if message.author.id == COUNTING_BOT_ID:
            assert message.guild is not None
            if len(message.embeds) > 0:
                embed = message.embeds[0]
                type = self._get_embed_type(embed.title)
                if type is not None:
                    caller = self.waiting_commands.pop(f'{message.channel.id}{type}', None)
                    if caller is not None:
                        if type == 'server':
                            lines: list[str] = embed.description.split('\n')
                            saves_line = lines[2]
                            saves = float(saves_line
                                          .removeprefix('Guild Saves: **')
                                          .removesuffix('/2**'))
                            async with self.data.guilds:
                                data = await self.data.get_guild(message.guild.id)
                                data['saves'] = saves
                            await self.check_all_members(message.guild)
                        elif type == 'user':
                            embed_value = embed.fields[0].value
                            if isinstance(embed_value, str):
                                lines: list[str] = embed_value.split('\n')
                                saves_line = lines[4]
                                saves = float(saves_line
                                            .removeprefix('Saves: **')
                                            .removesuffix('/3**'))
                                async with self.data.users:
                                    data = await self.data.get_user(caller.author.id)
                                    data['saves'] = saves
                                if isinstance(caller.author, discord.Member):
                                    try:
                                        await self.check_if_member_can_count(caller.author)
                                    except HTTPException:
                                        logging.warning('User %s left guild before c!user response', caller.author)
        elif message.content.startswith('c!'):
            type = message.content.split(None, 1)[0][2:]
            if type in VALID_COMMANDS:
                self.waiting_commands.add(f'{message.channel.id}{type}', message)

    async def check_if_member_can_count(self, member: discord.Member) -> bool:
        async def get_guild_data() -> tuple[float, int]:
            async with self.data.guilds:
                data = await self.data.get_guild(member.guild.id)
                return data['saves'], data['can_count_role']
        async def get_user_saves() -> float:
            async with self.data.users:
                return (await self.data.get_user(member.id))['saves']
        user_saves, (guild_saves, can_count_role) = await asyncio.gather(
            get_user_saves(),
            get_guild_data(),
        )
        total_saves = user_saves + guild_saves
        can_count = total_saves >= 1
        if can_count_role != 0:
            can_count_role = discord.Object(can_count_role)
            if can_count:
                await member.add_roles(can_count_role)
            else:
                await member.remove_roles(can_count_role)
        return can_count

    async def check_all_members(self, guild: discord.Guild) -> int:
        return sum(await asyncio.gather(*(
            self.check_if_member_can_count(member)
            for member in guild.members
            if not member.bot
        )))
