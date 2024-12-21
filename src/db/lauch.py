from config import config
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient


async def initialize():
    client = AsyncIOMotorClient(
        config.mongo_url,
        uuidRepresentation='standard'
    )

    await init_beanie(
        database=client.ReDirectBot,
        document_models=['src.db.models.Guild']
    )

    print('Database initialized')
