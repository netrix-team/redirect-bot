import asyncio

import disnake
from disnake.ext import commands

from .db.func import get_guild_model

# (10MB = 10 * 1024 * 1024 B)
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

        if message.author.bot and not any(
            target.settings.allowed_bots
            for target in channel_data.targets):

            return

        for target in channel_data.targets:
            settings = target.settings

            if settings.content_type == 1 and message.content.strip() == '':
                continue  # Text only, but the message does not contain text
            if settings.content_type == 2 and not message.attachments:
                continue  # Only files, but the message contains no attachments
            if settings.content_type == 3 and not message.embeds:
                continue  # Only embeds, but the message doesn't contain them
            if settings.content_type == 4 and not (
                message.content.strip() or message.attachments):
                continue  # Text and files, but the message is blank
            if settings.content_type == 5 and not (
                message.content.strip() or message.embeds):
                continue  # Text and embeds, but the message contains neither
            if settings.content_type == 6 and not (
                message.attachments or message.embeds):
                continue  # Files and embeds, but there aren't any

            allowed_attachments = []
            if settings.allowed_extensions is not None:
                for attachment in message.attachments:
                    if (any(attachment.filename.endswith(ext)
                            for ext in settings.allowed_extensions)
                            and attachment.size <= DISCORD_MAX_FILE_SIZE):
                        allowed_attachments.append(attachment)
            else:
                allowed_attachments = [
                    attachment for attachment in message.attachments
                    if attachment.size <= DISCORD_MAX_FILE_SIZE
                ]

            if settings.content_type in [2, 4, 6] and not allowed_attachments:
                continue

            target_channel = self.bot.get_channel(target.id)
            if not target_channel:
                continue

            target_guild = target_channel.guild

            if target_guild.id == guild_id:
                await self.handle_message(
                    message, allowed_attachments, target_channel)
                continue

            target_guild_model = await get_guild_model(target_guild.id)

            if not target_guild_model:
                continue

            whitelist_ids = {element.id for element
                             in target_guild_model.whitelist}
            if guild_id not in whitelist_ids:
                continue

            await self.handle_message(
                message, allowed_attachments, target_channel)

    async def handle_message(
        self, message: disnake.Message,
        attachments: list[disnake.Attachment],
        target_channel: disnake.TextChannel
    ):
        """
        Logic of message processing
        Forwarding messages to other channels
        """
        send_args = {}

        # Sending text
        if message.content:
            send_args['content'] = message.content

        # File preparation
        if attachments:
            send_args['files'] = await asyncio.gather(
                *(attachment.to_file() for attachment in attachments)
            )

        # Sending embeds
        if message.embeds:
            send_args['embeds'] = [embed.copy() for embed in message.embeds]

        if not send_args:
            return

        try:
            # Sending a message
            await target_channel.send(**send_args)

        except disnake.errors.HTTPException as ext:
            print(f'Failed to send a message in {target_channel.id}: {ext}')
