from disnake.ext import commands

from .source import Source
from .target import Target
from .owner import ForOwner

from .gHandler import GuildHandler
from .mHandler import MessageHandler


def setup(bot: commands.InteractionBot):

    bot.add_cog(Source(bot))
    bot.add_cog(Target(bot))
    bot.add_cog(ForOwner(bot))

    bot.add_cog(GuildHandler(bot))
    bot.add_cog(MessageHandler(bot))
