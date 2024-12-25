import asyncio
from os import listdir
from config import config

import disnake
from disnake.ext import commands
from disnake.flags import Intents

from src.db.lauch import initialize

from logger import get_logger
logger = get_logger(__name__)

intents = Intents.default()

intents.guilds = True
intents.members = True
intents.message_content = True


class ReDirect(commands.InteractionBot):
    def __init__(self):
        super().__init__(
            intents=intents
        )

    def load_extensions(self, path: str):
        excludes = ['db', 'utils']

        for file in listdir(f'./{path}'):
            if file not in excludes and file.endswith('.py'):
                try:
                    self.load_extension(f'{path}.{file[:-3]}')

                except commands.ExtensionNotFound as exc:
                    logger.error(exc)
                except commands.NoEntryPointError as exc:
                    logger.error(exc)
                except Exception as exc:
                    logger.error(exc)

    async def on_ready(self):
        print(f'BOT: {self.user}')
        print(f'ID: {self.user.id}')
        print(f'API VERSION: {disnake.__version__}')


async def main():
    bot = ReDirect()
    TOKEN = config.token

    # database
    await initialize()

    bot.load_extension('src')
    await bot.start(token=TOKEN)


if __name__ == '__main__':
    asyncio.run(main())
