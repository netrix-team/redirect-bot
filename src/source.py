import disnake
from disnake.ext import commands

from .db.func import get_guild_model
from .db.models import SourceChannel


class Source(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot

    @commands.has_permissions(administrator=True)
    @commands.slash_command(name='source', dm_permission=False)
    async def source(self, inter: disnake.ApplicationCommandInteraction):
        return
    
    @source.sub_command('add', 'Add a new source channel')
    async def source_add(self, inter: disnake.ApplicationCommandInteraction,
        source: disnake.TextChannel = commands.Param(
            description='Source channel to add')
    ):
        await inter.response.defer(ephemeral=True)

        guild = await get_guild_model(inter.guild.id)
        if not guild:
            return await inter.edit_original_response(
                content='📛 Guild not found in the database')
        
        if any(source.id == channel.id for channel in guild.channels):
            return await inter.edit_original_response(
                content='📛 The source channel already exists in the database')
        
        guild.channels.append(SourceChannel(id=source.id, name=source.name))
        await guild.save()

        await inter.edit_original_response(
            content=f'✅ Successfully added source channel {source.mention}')
        
    @source.sub_command('links', 'View current source channel links')
    async def source_links(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)

        guild = await get_guild_model(inter.guild.id)
        if not guild:
            return await inter.edit_original_response(
                content='📛 Guild not found in the database')
        
        if not guild.channels:
            return await inter.edit_original_response(
                content='📛 No links channels are configured')
        
        def build_ascii_tree(source: str, targets: list[str] = None):
            if not targets:
                return source

            lines = [source]
            for i, target in enumerate(targets):
                connector = '└─ ' if i == len(targets) - 1 else '├─ '
                lines.append(f'{connector}{target}')
            return '\n'.join(lines)
        
        descriptions: list = []
        for channel in guild.channels:
            targets = [t.name for t in channel.targets]
            tree_str = build_ascii_tree(channel.name, targets)
            descriptions.append(tree_str)

        if descriptions:
            result = '\n\n'.join(descriptions)
        else:
            result = 'No links available'

        await inter.edit_original_response(content=f'```\n{result}\n```')

    @source.sub_command('remove', 'Remove a source channel')
    async def source_remove(self, inter: disnake.ApplicationCommandInteraction,
        source: str = commands.Param(description='Source channel to remove')
    ):
        await inter.response.defer(ephemeral=True)

        guild = await get_guild_model(inter.guild.id)
        if not guild:
            return await inter.edit_original_response(
                content='📛 Guild not found in the database')
        
        if not guild.channels:
            return await inter.edit_original_response(
                content='📛 No links channels are configured')
        
        channel_to_remove = next(
            (ch for ch in guild.channels 
            if ch.name == source), None)

        if not channel_to_remove:
            return await inter.edit_original_response(
                content='📛 Source channel not found in the database')
        
        guild.channels.remove(channel_to_remove)
        await guild.save()

        await inter.edit_original_response(
            content=('✅ Successfully removed source '
                     f'channel <#{channel_to_remove.id}>'))

    @source_remove.autocomplete('source')
    async def source_remove_autocomplete(self,
        inter: disnake.ApplicationCommandInteraction, user_input: str
    ):
        guild = await get_guild_model(inter.guild.id)
        if not guild or not guild.channels:
            return []

        return [
            ch.name for ch in guild.channels
            if user_input.lower() in ch.name.lower()
        ][:25]
