from models import GuildActions, GuildConfig, ScamResult
from config.defaults import DEFAULT_THRESHOLD, DEFAULT_SCAN_MODE


def test_scam_result_fields():
    r = ScamResult(is_scam=True, confidence=90, reason="fake giveaway")
    assert r.is_scam is True
    assert r.confidence == 90
    assert r.reason == "fake giveaway"


def test_guild_actions_defaults():
    a = GuildActions()
    assert a.warn is True
    assert a.delete is True
    assert a.timeout_minutes == 0
    assert a.ban is False
    assert a.log_clean is False


def test_guild_actions_round_trip():
    a = GuildActions(warn=True, delete=False, timeout_minutes=10, ban=True, log_clean=True)
    d = a.to_dict()
    restored = GuildActions.from_dict(d)
    assert restored == a


def test_guild_config_defaults():
    c = GuildConfig(guild_id="123")
    assert c.guild_id == "123"
    assert c.log_channel_id is None
    assert c.scan_mode == DEFAULT_SCAN_MODE
    assert c.confidence_threshold == DEFAULT_THRESHOLD
    assert isinstance(c.actions, GuildActions)


def test_guild_config_round_trip():
    c = GuildConfig(
        guild_id="456",
        log_channel_id="789",
        scan_mode="all_images",
        confidence_threshold=80,
        actions=GuildActions(warn=False, delete=True, timeout_minutes=5, ban=False, log_clean=True),
    )
    d = c.to_dict()
    restored = GuildConfig.from_dict(d)
    assert restored == c


def test_guild_config_from_dict_ignores_mongo_id():
    d = {
        "_id": "some_mongo_id",
        "guild_id": "123",
        "log_channel_id": None,
        "scan_mode": "bro_only",
        "confidence_threshold": 75,
        "actions": {"warn": True, "delete": True, "timeout_minutes": 0, "ban": False, "log_clean": False},
    }
    c = GuildConfig.from_dict(d)
    assert c.guild_id == "123"
