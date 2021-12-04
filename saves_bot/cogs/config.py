import discord
from discord.ext import commands
from discord.role import Role
from saves_bot.cogs import BaseCog
from saves_bot.data import GuildData
from saves_bot.messages import CANNOT_BE_USED_IN_DM, UPDATED_ALLOWED_TO_COUNT


class ConfigCog(BaseCog):
    __cog_name__ = 'Configuration'

    @commands.command(
        name='count-role',
        brief='Sets the role given to people who are allowed to count',
    )
    @commands.has_guild_permissions(manage_roles=True)
    async def set_count_role_command(self, ctx: commands.Context, count_role: Role) -> None:
        if ctx.guild is None:
            await ctx.send(CANNOT_BE_USED_IN_DM)
            return
        data = self.bot.data
        async with data.guilds:
            (await data.get_guild(ctx.guild.id))['can_count_role'] = count_role.id
        await (
            await ctx.send(UPDATED_ALLOWED_TO_COUNT)
        ).edit(content=f'{UPDATED_ALLOWED_TO_COUNT} {count_role.mention}')

    @commands.command(
        name='guild-info',
    )
    async def guild_info_command(self, ctx: commands.Context) -> None:
        if ctx.guild is None:
            await ctx.send(CANNOT_BE_USED_IN_DM)
            return
        data = self.bot.data
        async with data.guilds:
            guild_data = await data.get_guild(ctx.guild.id)
            guild_saves, can_count_role = guild_data['saves'], guild_data['can_count_role']
        embed = discord.Embed(
            title='The following information is known about this guild',
            description=f'Guild Saves: {guild_saves}\nCan Count Role: <@&{can_count_role}>'
        )
        await ctx.send(embed=embed)
