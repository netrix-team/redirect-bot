import disnake
from disnake.ext import commands
from disnake.ext.commands import CommandError

from .db.func import get_guild_model
from .db.models import WhiteListElement


class WhiteList(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot

    @commands.has_permissions(administrator=True)
    @commands.slash_command(name='whitelist', dm_permission=False)
    async def whitelist(self, _: disnake.ApplicationCommandInteraction):
        return
    
    @whitelist.error
    async def whitelist_error(
        self, inter: disnake.ApplicationCommandInteraction,
        error: CommandError
    ):
        if isinstance(error, commands.MissingPermissions):
            return await inter.response.send_message(
                '📛 This command is not available to you!', ephemeral=True)

    @whitelist.sub_command(
        name='add',
        description=disnake.Localized('Add new guild to whitelist', data={
            disnake.Locale.uk: 'Додати новий сервер у вайтлист',
            disnake.Locale.ru: 'Добавить новый сервер в вайтлист'
        })
    )
    async def add(
        self, inter: disnake.ApplicationCommandInteraction,
        guild_id: int = commands.Param(
            description=disnake.Localized(
                'Guild ID to add', data={
                    disnake.Locale.uk: 'ID сервера, для додавання',
                    disnake.Locale.ru: 'ID сервера для добавления'
                }),
            ge=0,
            large=True,
            max_length=25
        )
    ):
        await inter.response.defer(ephemeral=True)

        guild = await get_guild_model(inter.guild.id)
        if guild is None:
            return await inter.edit_original_response(
                content='📛 This guild not found!')
        
        existing_guild_ids = {element.id for element in guild.whitelist}
        if guild_id in existing_guild_ids:
            return await inter.edit_original_response(
                content='📛 Guild already in whitelist')
        
        guilds = {guild.id for guild in self.bot.guilds}
        if guild_id not in guilds:
            return await inter.edit_original_response(
                content='📛 The bot must be present at the specified guild')
        
        guild_obj = self.bot.get_guild(guild_id)

        guild.whitelist.append(WhiteListElement(
            id=guild_obj.id, name=guild_obj.name)
        )
        await guild.save()

        await inter.edit_original_response('✅ Successful guild update')

    @whitelist.sub_command(
        name='list',
        description=disnake.Localized('Viewing the current list', data={
            disnake.Locale.uk: 'Перегляд поточного списку',
            disnake.Locale.ru: 'Просмотр текущего списка'
        })
    )
    async def list(
        self, inter: disnake.ApplicationCommandInteraction
    ):
        await inter.response.defer(ephemeral=True)

        guild = await get_guild_model(inter.guild.id)
        if guild is None:
            return await inter.edit_original_response(
                content='📛 This guild not found!')

        description: str = ''
        whitelist = guild.whitelist

        if not whitelist:
            return await inter.edit_original_response(
                content='📛 WhiteList is empty')

        for i, element in enumerate(whitelist):
            description += f'`#{i+1}` {element.name} ({element.id})\n'

        embed = disnake.Embed(
            title='Current WhiteList', description=description, colour=0x2b2d31
        )

        await inter.edit_original_response(embed=embed)

    @whitelist.sub_command(
        name='remove',
        description=disnake.Localized('Remove guild from whitelist', data={
            disnake.Locale.uk: 'Видалити сервер з вайтлиста',
            disnake.Locale.ru: 'Удалить сервер из вайтлиста'
        })
    )
    async def remove(
        self, inter: disnake.ApplicationCommandInteraction,
        guild_id: int = commands.Param(
            description=disnake.Localized(
                'Guild ID to remove', data={
                    disnake.Locale.uk: 'ID сервера для видалення',
                    disnake.Locale.ru: 'ID сервера для удаления'
                }),
            ge=0,
            large=True,
            max_length=25
        )
    ):
        await inter.response.defer(ephemeral=True)

        guild = await get_guild_model(inter.guild.id)
        if guild is None:
            return await inter.edit_original_response(
                content='📛 This guild not found!')

        whitelist = guild.whitelist

        for element in whitelist:
            if element.id == guild_id:
                whitelist.remove(element)
                await guild.save()

                return await inter.edit_original_response(
                    content='✅ Guild successfully removed from whitelist')

        return await inter.edit_original_response(
            content='📛 Guild not found in whitelist')
