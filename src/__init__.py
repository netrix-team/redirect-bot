from disnake.ext import commands

from .source import Source
from .target import Target

from .stats import Stats
from .whitelist import WhiteList

from .gHandler import GuildHandler
from .mHandler import MessageHandler


def setup(bot: commands.InteractionBot):

    bot.add_cog(Source(bot))
    bot.add_cog(Target(bot))

    bot.add_cog(Stats(bot))
    bot.add_cog(WhiteList(bot))

    bot.add_cog(GuildHandler(bot))
    bot.add_cog(MessageHandler(bot))
