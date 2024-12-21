import asyncio

import disnake
from disnake.ext import commands

from .db.func import get_guild_model

# Добавьте проверку размера файла (10MB = 10 * 1024 * 1024 байт)
DISCORD_MAX_FILE_SIZE = 10 * 1024 * 1024


class MessageHandler(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        guild_id = message.guild.id if message.guild else None
        if not guild_id:
            return
        
        guild = await get_guild_model(guild_id)
        if not guild:
            return
        
        channel_data = next((ch for ch in guild.channels
                             if ch.id == message.channel.id), None)
        if not channel_data:
            return

        if message.author.bot and not any(target.settings.allowed_bots for target in channel_data.targets):
            return

        for target in channel_data.targets:
            # Проверяем настройки целевого канала
            settings = target.settings

            if settings.content_type == 1 and message.content.strip() == '':
                continue  # Только текст, но сообщение не содержит текста
            if settings.content_type == 2 and not message.attachments:
                continue  # Только файлы, но сообщение не содержит вложений
            if settings.content_type == 3 and not message.embeds:
                continue  # Только ембеды, но сообщение их не содержит
            if settings.content_type == 4 and not (message.content.strip() or message.attachments):
                continue  # Текст и файлы, но сообщение пустое
            if settings.content_type == 5 and not (message.content.strip() or message.embeds):
                continue  # Текст и ембеды, но сообщение не содержит ни того, ни другого
            if settings.content_type == 6 and not (message.attachments or message.embeds):
                continue  # Файлы и ембеды, но их нет

            # Проверяем файлы на разрешённые расширения и размер
            allowed_attachments = []
            if settings.allowed_extensions is not None:
                for attachment in message.attachments:
                    if (any(attachment.filename.endswith(ext) for ext in settings.allowed_extensions)
                            and attachment.size <= DISCORD_MAX_FILE_SIZE):
                        allowed_attachments.append(attachment)
            else:
                # Если расширения не заданы, пропускаем только по размеру
                allowed_attachments = [
                    attachment for attachment in message.attachments if attachment.size <= DISCORD_MAX_FILE_SIZE
                ]

            # Если все файлы не подходят, но вложения требуются, пропускаем текущую итерацию
            if settings.content_type in [2, 4, 6] and not allowed_attachments:
                continue

            target_channel = self.bot.get_channel(target.id)
            if not target_channel:
                continue

            target_guild = target_channel.guild

            # Если исходный и целевой каналы находятся в одной гильдии, пропускаем проверку вайтлиста
            if target_guild.id == guild_id:
                await self.handle_message(message, allowed_attachments, target_channel)
                continue

            target_guild_model = await get_guild_model(target_guild.id)

            if not target_guild_model:
                continue

            whitelist_ids = {element.id for element in target_guild_model.whitelist}
            if guild_id not in whitelist_ids:
                continue

            # Если гильдия источника не в белом списке целевой гильдии, сообщение не отправляется
            await self.handle_message(message, allowed_attachments, target_channel)

    async def handle_message(self, message: disnake.Message, attachments, target_channel):
        """
        Логика обработки сообщения.
        Пересылка сообщений в другие каналы.
        """
        send_args = {}

        # Отправляем текст
        if message.content:
            send_args['content'] = message.content

        # Подготовка файлов
        if attachments:
            send_args['files'] = await asyncio.gather(
                *(attachment.to_file() for attachment in attachments)
            )

        # Отправляем ембеды
        if message.embeds:
            send_args['embeds'] = [embed.copy() for embed in message.embeds]

        # Отправляем сообщение
        await target_channel.send(**send_args)
