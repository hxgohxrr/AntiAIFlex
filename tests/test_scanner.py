from unittest.mock import MagicMock

import pytest
from models import GuildActions, GuildConfig
from cogs.scanner import should_scan


def _make_message(content="", has_image=True, content_type="image/png"):
    attachment = MagicMock()
    attachment.content_type = content_type if has_image else "application/pdf"

    message = MagicMock()
    message.content = content
    message.attachments = [attachment] if has_image else []
    message.author = MagicMock()
    message.author.bot = False
    return message


def test_bro_only_mode_triggers_on_bro_with_image():
    message = _make_message(content="bro check this out", has_image=True)
    config = GuildConfig(guild_id="1", scan_mode="bro_only")
    assert should_scan(message, config) is True


def test_bro_only_mode_case_insensitive():
    message = _make_message(content="BRO look at this", has_image=True)
    config = GuildConfig(guild_id="1", scan_mode="bro_only")
    assert should_scan(message, config) is True


def test_bro_only_mode_no_trigger_without_bro():
    message = _make_message(content="hey check this out", has_image=True)
    config = GuildConfig(guild_id="1", scan_mode="bro_only")
    assert should_scan(message, config) is False


def test_bro_only_mode_no_trigger_without_image():
    message = _make_message(content="bro check this out", has_image=False)
    config = GuildConfig(guild_id="1", scan_mode="bro_only")
    assert should_scan(message, config) is False


def test_all_images_mode_triggers_on_any_image():
    message = _make_message(content="look at this", has_image=True)
    config = GuildConfig(guild_id="1", scan_mode="all_images")
    assert should_scan(message, config) is True


def test_all_images_mode_no_trigger_without_image():
    message = _make_message(content="look at this", has_image=False)
    config = GuildConfig(guild_id="1", scan_mode="all_images")
    assert should_scan(message, config) is False


def test_non_image_attachment_not_scanned():
    message = _make_message(content="bro look", has_image=True, content_type="application/pdf")
    config = GuildConfig(guild_id="1", scan_mode="bro_only")
    assert should_scan(message, config) is False
