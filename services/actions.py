import logging
from datetime import datetime, timedelta, timezone

from models import GuildConfig, ScamResult

logger = logging.getLogger(__name__)


async def execute_actions(message, result: ScamResult, config: GuildConfig) -> list[str]:
    taken: list[str] = []
    member = message.author

    if config.actions.warn:
        try:
            await member.send(
                f"Your message in {message.guild} was flagged as a potential scam "
                f"(confidence: {result.confidence}%).\nReason: {result.reason}"
            )
            taken.append("warn")
        except Exception as exc:
            logger.warning("warn failed: %s", exc)
            taken.append("warn: failed")

    if config.actions.delete:
        try:
            await message.delete()
            taken.append("delete")
        except Exception as exc:
            logger.warning("delete failed: %s", exc)
            taken.append("delete: failed")

    if config.actions.timeout_minutes > 0:
        try:
            until = datetime.now(timezone.utc) + timedelta(minutes=config.actions.timeout_minutes)
            await member.timeout(until, reason=f"AntiScam: {result.reason}")
            taken.append(f"timeout {config.actions.timeout_minutes}m")
        except Exception as exc:
            logger.warning("timeout failed: %s", exc)
            taken.append("timeout: failed")

    if config.actions.ban:
        try:
            await member.ban(reason=f"AntiScam: {result.reason}")
            taken.append("ban")
        except Exception as exc:
            logger.warning("ban failed: %s", exc)
            taken.append("ban: failed")

    return taken
