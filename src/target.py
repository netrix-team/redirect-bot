import i18n

import disnake
from disnake.ext import commands
from disnake.i18n import Localized
from disnake.ext.commands import CommandError

from .db.func import get_guild_model
from .db.models import TargetChannel, Settings
from .utils.interface import Interface, CONTENT_TYPE_MAPPING


class Target(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot

    @commands.has_permissions(administrator=True)
    @commands.slash_command(
        name=Localized(
            string='target',
            key='TARGET_COMMAND_NAME'
        ),
        dm_permission=False
    )
    async def target(self, inter: disnake.ApplicationCommandInteraction):
        return

    @target.error
    async def target_error(
        self,
        inter: disnake.ApplicationCommandInteraction,
        error: CommandError
    ):
        locale = str(inter.locale.name)

        if isinstance(error, commands.MissingPermissions):
            return await inter.response.send_message(
                i18n.t('global.errors.forbidden', locale=locale),
                ephemeral=True)

    @target.sub_command(
        name=Localized(
            string='add',
            key='TARGET_ADD_COMMAND_NAME'
        ),
        description=Localized(
            string='Add a new target channel to a source channel',
            key='TARGET_ADD_COMMAND_DESCRIPTION'
        )
    )
    async def target_add(self, inter: disnake.ApplicationCommandInteraction,
        source: str = commands.Param(
            name=Localized(
                string='source',
                key='TARGET_ADD_PARAM_SOURCE_NAME'
            ),
            description=Localized(
                string='Source channel to which the target will be added',
                key='TARGET_ADD_PARAM_SOURCE_DESCRIPTION'
            )
        ),
        target: int = commands.Param(
            name=Localized(
                string='target',
                key='TARGET_ADD_PARAM_TARGET_NAME'
            ),
            description=Localized(
                string='Channel ID to add',
                key='TARGET_ADD_PARAM_TARGET_DESCRIPTION'
            ), ge=0, large=True, max_length=25
        ),
        content_type: int = commands.Param(
            name=Localized(
                string='content_type',
                key='TARGET_ADD_PARAM_CONTENT_TYPE_NAME'
            ),
            description=Localized(
                string='Type of content to forward',
                key='TARGET_ADD_PARAM_CONTENT_TYPE_DESCRIPTION'
            ),
            choices={
                'Text Only': 1,
                'Files Only': 2,
                'Embeds Only': 3,
                'Text and Files': 4,
                'Text and Embeds': 5,
                'Files and Embeds': 6,
                'All Content': 7
            },
        ),
        allowed_bots: bool = commands.Param(
            default=False,
            name=Localized(
                string='allowed_bots',
                key='TARGET_ADD_PARAM_ALLOWED_BOTS_NAME'
            ),
            description=Localized(
                string='Whether to process bot messages',
                key='TARGET_ADD_PARAM_ALLOWED_BOTS_DESCRIPTION'
            )
        ),
        allowed_extensions: str = commands.Param(
            default=None,
            name=Localized(
                string='allowed_extensions',
                key='TARGET_ADD_PARAM_ALLOWED_EXTENSIONS_NAME'
            ),
            description=Localized(
                string=('Comma-separated list of '
                        'allowed file extensions (leave blank for all)'),
                key='TARGET_ADD_PARAM_ALLOWED_EXTENSIONS_DESCRIPTION'
            )
        )
    ):
        locale = str(inter.locale.name)
        await inter.response.defer(ephemeral=True)

        guild = await get_guild_model(inter.guild.id)
        if not guild:
            return await inter.edit_original_response(
                content=i18n.t('global.errors.guild_not_found', locale=locale)
            )

        source_channel = next(
            (ch for ch in guild.channels
            if ch.name == source), None)

        if not source_channel:
            return await inter.edit_original_response(
                content=i18n.t('source.errors.source_not_found', locale=locale)
            )

        target_channel = None

        try:
            target_channel = (self.bot.get_channel(target)
                              or await self.bot.fetch_channel(target))

        except (ValueError, disnake.NotFound):
            return await inter.edit_original_response(
                content=i18n.t('target.errors.invalid_target_channel',
                               locale=locale)
            )

        allowed_extensions_list = (
            [ext.strip() for ext in allowed_extensions.split(',')
            if ext.strip()] if allowed_extensions else None
        )

        if any(t.id == target_channel.id for t in source_channel.targets):
            return await inter.edit_original_response(
                content=i18n.t('target.errors.target_exists', locale=locale)
            )

        if target_channel.guild.id != inter.guild.id:
            target_display = target_channel.jump_url
        else:
            target_display = target_channel.mention

        source_channel.targets.append(TargetChannel(
            id=target_channel.id,
            name=target_channel.name,
            settings=Settings(
                allowed_bots=allowed_bots,
                content_type=content_type,
                allowed_extensions=allowed_extensions_list
            )
        ))
        await guild.save()

        return await inter.edit_original_response(
            content=i18n.t(
                'target.success.target_added',
                locale=locale,
                target=target_display,
                source_id=source_channel.id
            )
        )

    @target_add.autocomplete('source')
    async def target_add_autocomplete(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user_input: str
    ):
        guild = await get_guild_model(inter.guild.id)
        if not guild or not guild.channels:
            return []

        return [
            ch.name for ch in guild.channels
            if user_input.lower() in ch.name.lower()
        ][:25]

    @target.sub_command(
        name=Localized(
            string='settings',
            key='TARGET_SETTINGS_COMMAND_NAME'
        ),
        description=Localized(
            string='View target channel settings',
            key='TARGET_SETTINGS_COMMAND_DESCRIPTION'
        )
    )
    async def target_settings(
        self,
        inter: disnake.ApplicationCommandInteraction,
        source: str = commands.Param(
            name=Localized(
                string='source',
                key='TARGET_SETTINGS_PARAM_SOURCE_NAME'
            ),
            description=Localized(
                string='Source channel to select',
                key='TARGET_SETTINGS_PARAM_SOURCE_DESCRIPTION'
            )
        ),
        target: str = commands.Param(
            name=Localized(
                string='target',
                key='TARGET_SETTINGS_PARAM_TARGET_NAME'
            ),
            description=Localized(
                string='Target channel to select',
                key='TARGET_SETTINGS_PARAM_TARGET_DESCRIPTION'
            )
        )
    ):
        locale = str(inter.locale.name)
        await inter.response.defer(ephemeral=True)

        guild = await get_guild_model(inter.guild.id)
        if not guild:
            return await inter.edit_original_response(
                content=i18n.t('global.errors.guild_not_found', locale=locale)
            )

        source_channel = next(
            (ch for ch in guild.channels
            if ch.name == source), None)

        if not source_channel:
            return await inter.edit_original_response(
                content=i18n.t('source.errors.source_not_found', locale=locale)
            )

        target_channel = next(
            (t for t in source_channel.targets
            if t.name == target), None)

        if not target_channel:
            return await inter.edit_original_response(
                content=i18n.t('target.errors.target_not_found', locale=locale)
            )

        settings = target_channel.settings

        embed = disnake.Embed(
            title='Target Channel Settings',
            description=('Settings for:\n'
                         f'**{target_channel.name}**'
                         f' (`{target_channel.id}`)'),
            colour=0x7f3bf5
        )
        embed.add_field(name='Allowed Bots',
            value=str(settings.allowed_bots), inline=False)

        embed.add_field(name='Content Type',
            value=CONTENT_TYPE_MAPPING[settings.content_type], inline=False)

        embed.add_field(name='Allowed Extensions',
            value=', '.join(settings.allowed_extensions)
            if settings.allowed_extensions else 'All', inline=False)

        view = Interface(settings, guild)
        await inter.edit_original_response(embed=embed, view=view)
        view.message = await inter.original_message()

    @target_settings.autocomplete('source')
    async def autocomplete_settings_sources(
        self, inter: disnake.ApplicationCommandInteraction, user_input: str
    ):
        guild = await get_guild_model(inter.guild.id)
        if not guild or not guild.channels:
            return []

        return [
            ch.name for ch in guild.channels
            if user_input.lower() in ch.name.lower()
        ][:25]

    @target_settings.autocomplete('target')
    async def autocomplete_settings_targets(
        self, inter: disnake.ApplicationCommandInteraction, user_input: str
    ):
        guild = await get_guild_model(inter.guild.id)
        if not guild or not guild.channels:
            return []

        selected_option = inter.options['settings']['source']

        source_channel = next(
            (ch for ch in guild.channels
            if ch.name == selected_option), None)

        if not source_channel:
            return []

        return [
            t.name for t in source_channel.targets
            if user_input.lower() in t.name.lower()
        ][:25]

    @target.sub_command(
        name=Localized(
            string='name',
            key='TARGET_REMOVE_COMMAND_NAME'
        ),
        description=Localized(
            string='Remove a target channel',
            key='TARGET_REMOVE_COMMAND_DESCRIPTION'
        )
    )
    async def target_remove(
        self,
        inter: disnake.ApplicationCommandInteraction,
        source: str = commands.Param(
            name=Localized(
                string='source',
                key='TARGET_REMOVE_PARAM_SOURCE_NAME'
            ),
            description=Localized(
                string='Source channel to select',
                key='TARGET_REMOVE_PARAM_SOURCE_DESCRIPTION'
            )
        ),
        target: str = commands.Param(
            name=Localized(
                string='target',
                key='TARGET_REMOVE_PARAM_TARGET_NAME'
            ),
            description=Localized(
                string='Target channel to select',
                key='TARGET_REMOVE_PARAM_TARGET_DESCRIPTION'
            )
        )
    ):
        locale = str(inter.locale.name)
        await inter.response.defer(ephemeral=True)

        guild = await get_guild_model(inter.guild.id)
        if not guild:
            return await inter.edit_original_response(
                content=i18n.t('global.errors.guild_not_found', locale=locale)
            )

        source_channel = next(
            (ch for ch in guild.channels
            if ch.name == source), None)

        if not source_channel:
            return await inter.edit_original_response(
                content=i18n.t('source.errors.source_not_found', locale=locale)
            )

        target_channel = next(
            (t for t in source_channel.targets
            if t.name == target), None)

        if not target_channel:
            return await inter.edit_original_response(
                content=i18n.t('target.errors.target_not_found', locale=locale)
            )

        source_channel.targets.remove(target_channel)
        await guild.save()

        return await inter.edit_original_response(
            content=i18n.t(
                'target.success.target_removed',
                locale=locale,
                target_name=target_channel.name,
                target_id=target_channel.id,
                source_id=source_channel.id
            )
        )

    @target_remove.autocomplete('source')
    async def autocomplete_remove_sources(
        self, inter: disnake.ApplicationCommandInteraction, user_input: str
    ):
        guild = await get_guild_model(inter.guild.id)
        if not guild or not guild.channels:
            return []

        return [
            ch.name for ch in guild.channels
            if user_input.lower() in ch.name.lower()
        ][:25]

    @target_remove.autocomplete('target')
    async def autocomplete_remove_targets(
        self, inter: disnake.ApplicationCommandInteraction, user_input: str
    ):
        guild = await get_guild_model(inter.guild.id)
        if not guild or not guild.channels:
            return []

        selected_option = inter.options['remove']['source']

        source_channel = next(
            (ch for ch in guild.channels
            if ch.name == selected_option), None)

        if not source_channel:
            return []

        return [
            t.name for t in source_channel.targets
            if user_input.lower() in t.name.lower()
        ][:25]
