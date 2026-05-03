import logging

import discord

from models import GuildConfig, ScamResult

logger = logging.getLogger(__name__)


def build_embed(
    message,
    result: ScamResult,
    actions_taken: list[str],
    config: GuildConfig,
) -> discord.Embed:
    if result.is_scam:
        embed = discord.Embed(
            title="🚨 Scam Detected",
            description=f"Confidence: {result.confidence}%",
            color=discord.Color.red(),
        )
        embed.add_field(name="User", value=str(message.author), inline=True)
        embed.add_field(name="Channel", value=message.channel.mention, inline=True)
        embed.add_field(name="Confidence", value=f"{result.confidence}%", inline=True)
        embed.add_field(name="Reason", value=result.reason, inline=False)
        embed.add_field(name="Actions", value=", ".join(actions_taken) or "none", inline=False)
        embed.add_field(name="Jump", value=f"[Message]({message.jump_url})", inline=False)
    else:
        embed = discord.Embed(
            title="✅ Image Analyzed — No Scam",
            color=discord.Color.green(),
        )
        embed.add_field(name="User", value=str(message.author), inline=True)
        embed.add_field(name="Channel", value=message.channel.mention, inline=True)
        embed.add_field(name="Confidence", value=f"{result.confidence}%", inline=True)

    image_url = next(
        (a.url for a in message.attachments if a.content_type and a.content_type.startswith("image/")),
        None,
    )
    if image_url:
        embed.set_thumbnail(url=image_url)

    embed.set_footer(text=f"AntiScamBot • threshold: {config.confidence_threshold}%")
    return embed


async def log_result(
    bot,
    message,
    result: ScamResult,
    actions_taken: list[str],
    config: GuildConfig,
) -> None:
    if config.log_channel_id is None:
        return
    if not result.is_scam and not config.actions.log_clean:
        return

    channel = bot.get_channel(int(config.log_channel_id))
    if channel is None:
        logger.warning("Log channel %s not found for guild %s", config.log_channel_id, config.guild_id)
        return

    embed = build_embed(message, result, actions_taken, config)
    try:
        await channel.send(embed=embed)
    except Exception as exc:
        logger.error("Failed to send log embed: %s", exc)
