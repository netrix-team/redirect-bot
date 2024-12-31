import re
import asyncio

import disnake
from disnake.ext import commands

from .db.func import get_guild_model

MAX_MESSAGE_LENGTH = 2000
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
        target_guild_emojis = {emoji.name: emoji for emoji
                               in target_channel.guild.emojis}

        new_content = self.replace_emojis_in_text(
            content=message.content, emojis=target_guild_emojis)

        new_content = self.format_message_content(
            content=new_content, jump_url=message.jump_url)

        send_args = {}

        # Sending text
        if new_content:
            send_args['content'] = new_content

        # File preparation
        if attachments:
            send_args['files'] = await asyncio.gather(
                *(attachment.to_file() for attachment in attachments)
            )

        # Sending embeds
        if message.embeds:
            embeds: list[disnake.Embed] = []
            for embed in message.embeds:

                updated_embed = embed.copy()
                if updated_embed.description:
                    updated_embed.description = self.replace_emojis_in_text(
                        content=embed.description, emojis=target_guild_emojis)

                embeds.append(updated_embed)
            send_args['embeds'] = embeds

        if not send_args:
            return

        try:
            # Sending a message
            await target_channel.send(**send_args)

        except disnake.errors.HTTPException as ext:
            print(f'Failed to send a message in {target_channel.id}: {ext}')

    def replace_emojis_in_text(
        self,
        content: str,
        emojis: dict[str, disnake.Emoji]
    ) -> str:
        """
        Replaces emojis in the text with
        their corresponding guild-specific emojis
        """
        def replace_emojis(match: re.Match) -> str:
            emoji_name = match.group(1)
            if emoji_name in emojis:
                return f'<:{emoji_name}:{emojis[emoji_name].id}>'
            return match.group(0)

        emoji_pattern = r'<:([a-zA-Z0-9_]+):\d+>'
        return re.sub(emoji_pattern, replace_emojis, content)

    def format_message_content(self, content: str, jump_url: str) -> str:
        """
        Formats the message content to ensure
        it meets Discord's length constraints
        """
        url_length = len(jump_url)
        if len(content) + url_length + 10 > MAX_MESSAGE_LENGTH:
            truncation_limit = MAX_MESSAGE_LENGTH - url_length - 10

            lines = content.splitlines(keepends=True)
            truncated_content = ''
            current_length = 0

            for line in lines:
                if current_length + len(line) > truncation_limit - 3:
                    remaining_space = truncation_limit - 3 - current_length
                    words = line[:remaining_space].rsplit(maxsplit=1)

                    if len(words) > 1:
                        truncated_content += words[0] + ' '
                    break

                truncated_content += line
                current_length += len(line)

            return truncated_content.rstrip() + '...' + f'\n{jump_url}'

        else:
            return content
