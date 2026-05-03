from unittest.mock import AsyncMock, MagicMock

import discord
import pytest
from models import GuildConfig, ScamResult
from services.logger import build_embed, log_result


def _make_message(channel_id="333", author_name="TestUser#0001"):
    author = MagicMock()
    author.__str__ = lambda self: author_name

    channel = MagicMock()
    channel.mention = f"<#{channel_id}>"

    attachment = MagicMock()
    attachment.url = "https://cdn.discordapp.com/fake.png"
    attachment.content_type = "image/png"

    message = MagicMock()
    message.author = author
    message.channel = channel
    message.jump_url = "https://discord.com/channels/1/2/3"
    message.attachments = [attachment]
    return message


def test_build_embed_scam_is_red():
    message = _make_message()
    result = ScamResult(is_scam=True, confidence=90, reason="fake giveaway")
    config = GuildConfig(guild_id="222", confidence_threshold=75)
    actions_taken = ["warn", "delete"]

    embed = build_embed(message, result, actions_taken, config)

    assert embed.color == discord.Color.red()
    assert "90" in embed.description or any("90" in str(f.value) for f in embed.fields)


def test_build_embed_clean_is_green():
    message = _make_message()
    result = ScamResult(is_scam=False, confidence=12, reason="normal image")
    config = GuildConfig(guild_id="222", confidence_threshold=75)

    embed = build_embed(message, result, [], config)

    assert embed.color == discord.Color.green()


async def test_log_result_posts_to_channel():
    message = _make_message()
    result = ScamResult(is_scam=True, confidence=90, reason="fake giveaway")
    config = GuildConfig(guild_id="222", log_channel_id="555", confidence_threshold=75)
    actions_taken = ["warn", "delete"]

    log_channel = MagicMock()
    log_channel.send = AsyncMock()

    bot = MagicMock()
    bot.get_channel = MagicMock(return_value=log_channel)

    await log_result(bot, message, result, actions_taken, config)

    bot.get_channel.assert_called_once_with(555)
    log_channel.send.assert_awaited_once()


async def test_log_result_skips_clean_when_log_clean_false():
    message = _make_message()
    result = ScamResult(is_scam=False, confidence=10, reason="normal image")
    config = GuildConfig(guild_id="222", log_channel_id="555", confidence_threshold=75)

    log_channel = MagicMock()
    log_channel.send = AsyncMock()

    bot = MagicMock()
    bot.get_channel = MagicMock(return_value=log_channel)

    await log_result(bot, message, result, [], config)

    log_channel.send.assert_not_awaited()


async def test_log_result_logs_clean_when_enabled():
    message = _make_message()
    result = ScamResult(is_scam=False, confidence=10, reason="normal image")
    from models import GuildActions
    config = GuildConfig(
        guild_id="222",
        log_channel_id="555",
        confidence_threshold=75,
        actions=GuildActions(log_clean=True),
    )

    log_channel = MagicMock()
    log_channel.send = AsyncMock()

    bot = MagicMock()
    bot.get_channel = MagicMock(return_value=log_channel)

    await log_result(bot, message, result, [], config)

    log_channel.send.assert_awaited_once()
