from disnake import Guild
from disnake.ext import commands

from .db.func import get_guild_ids, get_guild_model, \
    update_guild_model, create_guild_model


class GuildHandler(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        active_guilds = await get_guild_ids()

        for guild in self.bot.guilds:
            if guild.id in active_guilds:
                continue

            model = create_guild_model(guild)
            await model.insert()

    @commands.Cog.listener()
    async def on_guild_join(self, guild: Guild):
        model = await get_guild_model(guild.id)
        if model is not None:
            return

        model = create_guild_model(guild)
        await model.insert()

    @commands.Cog.listener()
    async def on_guild_update(self, before: Guild, after: Guild):
        if before.name != after.name:
            await update_guild_model(after.id, name=after.name)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: Guild):
        model = await get_guild_model(guild.id)
        if model is None:
            return

        await model.delete()
