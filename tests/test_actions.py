from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from models import GuildActions, GuildConfig, ScamResult
from services.actions import execute_actions


def _make_message(author_id="111", guild_id="222"):
    member = MagicMock()
    member.id = author_id
    member.send = AsyncMock()
    member.timeout = AsyncMock()
    member.ban = AsyncMock()

    message = MagicMock()
    message.author = member
    message.delete = AsyncMock()
    message.guild = MagicMock()
    message.guild.id = guild_id
    return message


async def test_warn_sends_dm():
    message = _make_message()
    result = ScamResult(is_scam=True, confidence=90, reason="fake giveaway")
    config = GuildConfig(guild_id="222", actions=GuildActions(warn=True, delete=False))

    taken = await execute_actions(message, result, config)

    message.author.send.assert_awaited_once()
    assert "warn" in taken


async def test_delete_removes_message():
    message = _make_message()
    result = ScamResult(is_scam=True, confidence=90, reason="fake giveaway")
    config = GuildConfig(guild_id="222", actions=GuildActions(warn=False, delete=True))

    taken = await execute_actions(message, result, config)

    message.delete.assert_awaited_once()
    assert "delete" in taken


async def test_timeout_applies_duration():
    message = _make_message()
    result = ScamResult(is_scam=True, confidence=90, reason="fake giveaway")
    config = GuildConfig(guild_id="222", actions=GuildActions(warn=False, delete=False, timeout_minutes=10))

    taken = await execute_actions(message, result, config)

    message.author.timeout.assert_awaited_once()
    assert any("timeout" in t for t in taken)


async def test_ban_bans_user():
    message = _make_message()
    result = ScamResult(is_scam=True, confidence=90, reason="fake giveaway")
    config = GuildConfig(guild_id="222", actions=GuildActions(warn=False, delete=False, ban=True))

    taken = await execute_actions(message, result, config)

    message.author.ban.assert_awaited_once()
    assert "ban" in taken


async def test_no_actions_when_timeout_zero():
    message = _make_message()
    result = ScamResult(is_scam=True, confidence=90, reason="fake giveaway")
    config = GuildConfig(guild_id="222", actions=GuildActions(warn=False, delete=False, timeout_minutes=0, ban=False))

    taken = await execute_actions(message, result, config)

    message.author.timeout.assert_not_awaited()
    assert "timeout" not in taken


async def test_failed_action_recorded_as_failed(capsys):
    message = _make_message()
    message.delete = AsyncMock(side_effect=Exception("Missing Permissions"))
    result = ScamResult(is_scam=True, confidence=90, reason="fake giveaway")
    config = GuildConfig(guild_id="222", actions=GuildActions(warn=False, delete=True))

    taken = await execute_actions(message, result, config)

    assert any("delete" in t and "failed" in t for t in taken)
