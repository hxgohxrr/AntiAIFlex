from motor.motor_asyncio import AsyncIOMotorDatabase
from models import GuildConfig


async def get_config(db: AsyncIOMotorDatabase, guild_id: str) -> GuildConfig:
    doc = await db.guild_configs.find_one({"guild_id": guild_id})
    if doc is None:
        return GuildConfig(guild_id=guild_id)
    return GuildConfig.from_dict(doc)


async def upsert_config(db: AsyncIOMotorDatabase, config: GuildConfig) -> None:
    await db.guild_configs.update_one(
        {"guild_id": config.guild_id},
        {"$set": config.to_dict()},
        upsert=True,
    )
