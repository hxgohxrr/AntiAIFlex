import pytest
from models import GuildActions, GuildConfig
from db.guild_config import get_config, upsert_config


async def test_get_config_returns_default_when_missing(db):
    config = await get_config(db, "999")
    assert config.guild_id == "999"
    assert config.confidence_threshold == 85
    assert config.log_channel_id is None


async def test_upsert_and_get_config(db):
    config = GuildConfig(
        guild_id="123",
        log_channel_id="456",
        scan_mode="all_images",
        confidence_threshold=80,
        actions=GuildActions(warn=True, delete=True, timeout_minutes=10, ban=False, log_clean=True),
    )
    await upsert_config(db, config)
    retrieved = await get_config(db, "123")
    assert retrieved.log_channel_id == "456"
    assert retrieved.scan_mode == "all_images"
    assert retrieved.confidence_threshold == 80
    assert retrieved.actions.timeout_minutes == 10
    assert retrieved.actions.log_clean is True


async def test_upsert_overwrites_existing(db):
    config = GuildConfig(guild_id="123", confidence_threshold=70)
    await upsert_config(db, config)

    updated = GuildConfig(guild_id="123", confidence_threshold=90)
    await upsert_config(db, updated)

    retrieved = await get_config(db, "123")
    assert retrieved.confidence_threshold == 90
