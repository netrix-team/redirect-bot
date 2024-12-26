import i18n

import disnake
from disnake.ext import commands
from disnake.i18n import Localized
from disnake.ext.commands import CommandError

from .db.func import get_guild_model
from .db.models import SourceChannel


class Source(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot

    @commands.has_permissions(administrator=True)
    @commands.slash_command(
        name=Localized(
            string='source',
            key='SOURCE_COMMAND_NAME'
        ),
        dm_permission=False
    )
    async def source(self, inter: disnake.ApplicationCommandInteraction):
        return

    @source.error
    async def source_error(
        self,
        inter: disnake.ApplicationCommandInteraction,
        error: CommandError
    ):
        locale = str(inter.locale.name)

        if isinstance(error, commands.MissingPermissions):
            return await inter.response.send_message(
                i18n.t('errors.missing_permissions', locale=locale),
                ephemeral=True)

    @source.sub_command(
        name=Localized(
            string='add',
            key='SOURCE_ADD_COMMAND_NAME'
        ),
        description=Localized(
            string='Add a new source channel',
            key='SOURCE_ADD_COMMAND_DESCRIPTION'
        )
    )
    async def source_add(
        self,
        inter: disnake.ApplicationCommandInteraction,
        source: disnake.TextChannel = commands.Param(
            name=Localized(
                string='source',
                key='SOURCE_ADD_PARAM_SOURCE_NAME'
            ),
            description=Localized(
                string='Source channel to add',
                key='SOURCE_ADD_PARAM_SOURCE_DESCRIPTION'
            )
        )
    ):
        locale = str(inter.locale.name)
        await inter.response.defer(ephemeral=True)

        guild = await get_guild_model(inter.guild.id)
        if not guild:
            return await inter.edit_original_response(
                content=i18n.t('errors.guild_not_found', locale=locale)
            )

        if any(source.id == channel.id for channel in guild.channels):
            return await inter.edit_original_response(
                content=i18n.t('errors.source_exists', locale=locale)
            )

        guild.channels.append(SourceChannel(id=source.id, name=source.name))
        await guild.save()

        await inter.edit_original_response(
            content=i18n.t('success.source_added',
                locale=locale, channel=source.mention)
        )

    @source.sub_command(
        name=Localized(
            string='links',
            key='SOURCE_LINKS_COMMAND_NAME'
        ),
        description=Localized(
            string='View current source channel links',
            key='SOURCE_LINKS_COMMAND_DESCRIPTION'
        )
    )
    async def source_links(
        self,
        inter: disnake.ApplicationCommandInteraction
    ):
        locale = str(inter.locale.name)
        await inter.response.defer(ephemeral=True)

        guild = await get_guild_model(inter.guild.id)
        if not guild:
            return await inter.edit_original_response(
                content=i18n.t('errors.guild_not_found', locale=locale)
            )

        if not guild.channels:
            return await inter.edit_original_response(
                content=i18n.t('errors.no_links', locale=locale)
            )

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
            result = i18n.t('errors.no_links_available', locale=locale)

        await inter.edit_original_response(content=f'```\n{result}\n```')

    @source.sub_command(
        name=Localized(
            string='remove',
            key='SOURCE_REMOVE_COMMAND_NAME'
        ),
        description=Localized(
            string='Remove a source channel',
            key='SOURCE_REMOVE_COMMAND_DESCRIPTION'
        )
    )
    async def source_remove(
        self,
        inter: disnake.ApplicationCommandInteraction,
        source: str = commands.Param(
            name=Localized(
                string='source',
                key='SOURCE_REMOVE_PARAM_SOURCE_NAME'
            ),
            description=Localized(
                string='Source channel to remove',
                key='SOURCE_REMOVE_PARAM_SOURCE_DESCRIPTION'
            )
        )
    ):
        locale = str(inter.locale.name)
        await inter.response.defer(ephemeral=True)

        guild = await get_guild_model(inter.guild.id)
        if not guild:
            return await inter.edit_original_response(
                content=i18n.t('errors.guild_not_found', locale=locale)
            )

        if not guild.channels:
            return await inter.edit_original_response(
                content=i18n.t('errors.no_links', locale=locale)
            )

        channel_to_remove = next(
            (ch for ch in guild.channels
            if ch.name == source), None)

        if not channel_to_remove:
            return await inter.edit_original_response(
                content=i18n.t('errors.source_not_found', locale=locale)
            )

        guild.channels.remove(channel_to_remove)
        await guild.save()

        await inter.edit_original_response(
            content=i18n.t(
                'success.source_removed',
                locale=locale, channel_id=channel_to_remove.id
            )
        )

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
