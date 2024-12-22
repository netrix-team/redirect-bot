import disnake
from disnake.ext import commands


class ForOwner(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot

    @commands.slash_command(
        name='owner', description='View owner of the bot', dm_permission=False
    )
    async def botOwner(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)

        profile_url: str = 'https://discord.com/users/461219084802195477'
        message = f'Owner of the bot: [x4zx](<{profile_url}>)'
        await inter.edit_original_response(content=message)

