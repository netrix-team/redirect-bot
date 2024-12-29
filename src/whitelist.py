import i18n

import disnake
from disnake.ext import commands
from disnake.i18n import Localized
from disnake.ext.commands import CommandError

from .db.func import get_guild_model
from .db.models import WhiteListElement


class WhiteList(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot

    @commands.has_permissions(
        administrator=True
    )
    @commands.slash_command(
        name=Localized(
            string='whitelist',
            key='WHITELIST_COMMAND_NAME'
        ),
        description=Localized(
            string='Manage your guild whitelist',
            key='WHITELIST_COMMAND_DESCRIPTION'
        ),
        dm_permission=False
    )
    async def whitelist(self, _: disnake.ApplicationCommandInteraction):
        return

    @whitelist.error
    async def whitelist_error(
        self,
        inter: disnake.ApplicationCommandInteraction,
        error: CommandError
    ):
        locale = str(inter.locale.name)

        if isinstance(error, commands.MissingPermissions):
            return await inter.response.send_message(
                i18n.t('global.errors.forbidden', locale=locale),
                ephemeral=True)

    @whitelist.sub_command(
        name=Localized(
            string='add',
            key='WHITELIST_ADD_COMMAND_NAME'
        ),
        description=Localized(
            string='Add new guild to whitelist',
            key='WHITELIST_ADD_COMMAND_DESCRIPTION'
        )
    )
    async def add(
        self, inter: disnake.ApplicationCommandInteraction,
        guild_id: int = commands.Param(
            name=Localized(
                string='guild_id',
                key='WHITELIST_ADD_PARAM_GUILD_ID_NAME'
            ),
            description=Localized(
                string='Guild ID to add',
                key='WHITELIST_ADD_PARAM_GUILD_ID_DESCRIPTION'
            ),
            ge=0, large=True, max_length=25
        )
    ):
        locale = str(inter.locale.name)
        await inter.response.defer(ephemeral=True)

        guild = await get_guild_model(inter.guild.id)
        if not guild:
            return await inter.edit_original_response(
                content=i18n.t('global.errors.guild_not_found', locale=locale)
            )
        
        try:
            guild_id = int(guild_id)
        except ValueError:
            return await inter.edit_original_response(
                content=i18n.t(
                    'global.errors.invalid_guild_id',
                    locale=locale
                )
            )

        existing_guild_ids = {element.id for element in guild.whitelist}

        if guild_id in existing_guild_ids:
            return await inter.edit_original_response(
                content=i18n.t(
                    'whitelist.errors.guild_already_in_whitelist',
                    locale=locale
                )
            )

        guilds = {guild.id for guild in self.bot.guilds}
        if guild_id not in guilds:
            return await inter.edit_original_response(
                content=i18n.t('whitelist.errors.bot_not_present',
                               locale=locale)
            )

        guild_obj = self.bot.get_guild(guild_id)

        guild.whitelist.append(WhiteListElement(
            id=guild_obj.id, name=guild_obj.name)
        )
        await guild.save()

        return await inter.edit_original_response(
            content=i18n.t('whitelist.success.guild_added', locale=locale)
        )

    @whitelist.sub_command(
        name=Localized(
            string='list',
            key='WHITELIST_LIST_COMMAND_NAME'
        ),
        description=Localized(
            string='Viewing the current list',
            key='WHITELIST_LIST_COMMAND_DESCRIPTION'
        )
    )
    async def list(
        self, inter: disnake.ApplicationCommandInteraction
    ):
        locale = str(inter.locale.name)
        await inter.response.defer(ephemeral=True)

        guild = await get_guild_model(inter.guild.id)
        if not guild:
            return await inter.edit_original_response(
                content=i18n.t('global.errors.guild_not_found', locale=locale)
            )

        description: str = ''
        whitelist = guild.whitelist

        if not whitelist:
            return await inter.edit_original_response(
                content=i18n.t('whitelist.errors.whitelist_empty',
                               locale=locale)
            )

        for i, element in enumerate(whitelist):
            description += f'`#{i + 1}` {element.name} ({element.id})\n'

        embed = disnake.Embed(
            title=i18n.t('whitelist.info.current_whitelist', locale=locale),
            description=description, colour=0x2b2d31
        )

        await inter.edit_original_response(embed=embed)

    @whitelist.sub_command(
        name=Localized(
            string='remove',
            key='WHITELIST_REMOVE_COMMAND_NAME'
        ),
        description=Localized(
            string='Remove guild from whitelist',
            key='WHITELIST_REMOVE_COMMAND_DESCRIPTION'
        )
    )
    async def remove(
        self, inter: disnake.ApplicationCommandInteraction,
        guild_id: int = commands.Param(
            name=Localized(
                string='guild_id',
                key='WHITELIST_REMOVE_PARAM_GUILD_ID_NAME'
            ),
            description=Localized(
                string='Guild ID to remove',
                key='WHITELIST_REMOVE_PARAM_GUILD_ID_DESCRIPTION'
            ),
            ge=0, large=True, max_length=25
        )
    ):
        locale = str(inter.locale.name)
        await inter.response.defer(ephemeral=True)

        guild = await get_guild_model(inter.guild.id)
        if not guild:
            return await inter.edit_original_response(
                content=i18n.t('global.errors.guild_not_found', locale=locale)
            )
        
        try:
            guild_id = int(guild_id)
        except ValueError:
            return await inter.edit_original_response(
                content=i18n.t(
                    'global.errors.invalid_guild_id',
                    locale=locale
                )
            )

        whitelist = guild.whitelist

        for element in whitelist:
            if element.id == guild_id:
                whitelist.remove(element)
                await guild.save()

                return await inter.edit_original_response(
                    content=i18n.t('whitelist.success.guild_removed',
                                   locale=locale)
                )

        await inter.edit_original_response(
            content=i18n.t('whitelist.errors.guild_not_in_whitelist',
                           locale=locale)
        )
