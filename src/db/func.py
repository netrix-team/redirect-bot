from .models import Guild
from disnake import Guild as DiscordGuild


async def get_guild_ids() -> set:
    guilds = await Guild.find({}).to_list()
    ids = {guild.id for guild in guilds}
    return ids


async def get_guild_model(guild_id: int) -> Guild | None:
    guild = await Guild.find_one(Guild.id == guild_id)
    return guild if guild else None


async def update_guild_model(guild_id: int, **kwargs) -> bool:
    guild = await get_guild_model(guild_id)
    if guild is None:
        return False

    updates = {
        field: value for field, value in kwargs.items()
        if field != 'id' and hasattr(guild, field)
        and getattr(guild, field) != value
    }

    if updates:
        for field, value in updates.items():
            setattr(guild, field, value)
        await guild.save()

    return bool(updates)


def create_guild_model(guild: DiscordGuild) -> Guild:
    model = Guild(id=guild.id, name=guild.name, owner=guild.owner.id)
    return model
