import i18n

import disnake
from disnake.ext import commands
from disnake.i18n import Localized


class Stats(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot

    @commands.slash_command(
        name=Localized(
            string='stats',
            key='STATS_COMMAND_NAME'
        ),
        description=Localized(
            string='Show bot stats',
            key='STATS_COMMAND_DESCRIPTION'
        )
    )
    async def stats(self, inter: disnake.ApplicationCommandInteraction):
        locale = str(inter.locale.name)
        await inter.response.defer(ephemeral=True)

        guilds = self.bot.guilds
        gCount = len(guilds)

        members = sum(guild.member_count for guild in guilds)
        channels = sum(len(guild.channels) for guild in guilds)
        created_at = self.bot.user.created_at.strftime('%Y-%m-%d %H:%M:%S')

        emb = disnake.Embed(
            title=i18n.t(
                'stats.info.title',
                locale=locale
            ),
            colour=0x7f3bf5
        )

        fields = [
            (i18n.t('stats.info.guilds', locale=locale), gCount),
            (i18n.t('stats.info.members', locale=locale), members),
            (i18n.t('stats.info.channels', locale=locale), channels),
            (i18n.t('stats.info.created_at', locale=locale), created_at),
            (i18n.t('stats.info.developer', locale=locale), 'x4zx'),
        ]

        for name, value in fields:
            emb.add_field(
                name=f'> {name}',
                value=f'```{value}```',
                inline=True
            )

        emb.set_thumbnail(
            url=self.bot.user.avatar.url
            if self.bot.user.avatar else None
        )

        emb.set_footer(
            text=i18n.t(
                'stats.info.requested_by',
                locale=locale,
                username=inter.author.display_name
            ),

            icon_url=inter.author.avatar.url
            if inter.author.avatar else None
        )

        await inter.edit_original_response(embed=emb)
