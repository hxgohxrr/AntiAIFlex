from dataclasses import asdict, dataclass, field
from config.defaults import DEFAULT_SCAN_MODE, DEFAULT_THRESHOLD


@dataclass
class ScamResult:
    is_scam: bool
    confidence: int
    reason: str


@dataclass
class GuildActions:
    warn: bool = True
    delete: bool = True
    timeout_minutes: int = 0
    ban: bool = False
    log_clean: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "GuildActions":
        return cls(
            warn=d.get("warn", True),
            delete=d.get("delete", True),
            timeout_minutes=d.get("timeout_minutes", 0),
            ban=d.get("ban", False),
            log_clean=d.get("log_clean", False),
        )


@dataclass
class GuildConfig:
    guild_id: str
    log_channel_id: str | None = None
    scan_mode: str = DEFAULT_SCAN_MODE
    confidence_threshold: int = DEFAULT_THRESHOLD
    actions: GuildActions = field(default_factory=GuildActions)

    def to_dict(self) -> dict:
        return {
            "guild_id": self.guild_id,
            "log_channel_id": self.log_channel_id,
            "scan_mode": self.scan_mode,
            "confidence_threshold": self.confidence_threshold,
            "actions": self.actions.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "GuildConfig":
        d = dict(d)
        d.pop("_id", None)
        actions_data = d.pop("actions", {})
        return cls(**d, actions=GuildActions.from_dict(actions_data))
