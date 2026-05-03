import discord
from discord import app_commands
from discord.ext import commands

from db.client import get_db
from db.guild_config import get_config, upsert_config
from models import GuildConfig


def _require_manage_guild():
    async def predicate(interaction: discord.Interaction) -> bool:
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(
                "You need **Manage Server** permission to use this command.", ephemeral=True
            )
            return False
        return True
    return app_commands.check(predicate)


antiscam = app_commands.Group(name="antiscam", description="AntiScam bot configuration")
action_group = app_commands.Group(name="action", description="Configure moderation actions", parent=antiscam)


@antiscam.command(name="setup", description="Set the log channel (enables the bot for this server)")
@_require_manage_guild()
async def cmd_setup(interaction: discord.Interaction, channel: discord.TextChannel) -> None:
    db = get_db()
    config = await get_config(db, str(interaction.guild_id))
    config.log_channel_id = str(channel.id)
    await upsert_config(db, config)
    await interaction.response.send_message(
        f"AntiScam enabled. Logs will be posted in {channel.mention}.", ephemeral=True
    )


@antiscam.command(name="mode", description="Set scan trigger mode")
@_require_manage_guild()
@app_commands.choices(scan_mode=[
    app_commands.Choice(name="Bro + image (default)", value="bro_only"),
    app_commands.Choice(name="All images", value="all_images"),
])
async def cmd_mode(interaction: discord.Interaction, scan_mode: app_commands.Choice[str]) -> None:
    db = get_db()
    config = await get_config(db, str(interaction.guild_id))
    config.scan_mode = scan_mode.value
    await upsert_config(db, config)
    await interaction.response.send_message(f"Scan mode set to **{scan_mode.name}**.", ephemeral=True)


@antiscam.command(name="threshold", description="Set minimum confidence % to act (default: 75)")
@_require_manage_guild()
async def cmd_threshold(interaction: discord.Interaction, value: int) -> None:
    if not 0 <= value <= 100:
        await interaction.response.send_message("Threshold must be between 0 and 100.", ephemeral=True)
        return
    db = get_db()
    config = await get_config(db, str(interaction.guild_id))
    config.confidence_threshold = value
    await upsert_config(db, config)
    await interaction.response.send_message(f"Confidence threshold set to **{value}%**.", ephemeral=True)


@antiscam.command(name="status", description="Show current configuration")
async def cmd_status(interaction: discord.Interaction) -> None:
    db = get_db()
    config = await get_config(db, str(interaction.guild_id))
    log_ch = f"<#{config.log_channel_id}>" if config.log_channel_id else "not set"
    embed = discord.Embed(title="AntiScam Configuration", color=discord.Color.blurple())
    embed.add_field(name="Log Channel", value=log_ch, inline=True)
    embed.add_field(name="Scan Mode", value=config.scan_mode, inline=True)
    embed.add_field(name="Threshold", value=f"{config.confidence_threshold}%", inline=True)
    embed.add_field(name="Warn", value="✅" if config.actions.warn else "❌", inline=True)
    embed.add_field(name="Delete", value="✅" if config.actions.delete else "❌", inline=True)
    embed.add_field(name="Timeout", value=f"{config.actions.timeout_minutes}m" if config.actions.timeout_minutes else "❌", inline=True)
    embed.add_field(name="Ban", value="✅" if config.actions.ban else "❌", inline=True)
    embed.add_field(name="Log Clean", value="✅" if config.actions.log_clean else "❌", inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@action_group.command(name="warn", description="Toggle warn DM on scam detection")
@_require_manage_guild()
@app_commands.choices(enabled=[
    app_commands.Choice(name="On", value=1),
    app_commands.Choice(name="Off", value=0),
])
async def cmd_action_warn(interaction: discord.Interaction, enabled: app_commands.Choice[int]) -> None:
    db = get_db()
    config = await get_config(db, str(interaction.guild_id))
    config.actions.warn = bool(enabled.value)
    await upsert_config(db, config)
    await interaction.response.send_message(f"Warn DM: **{'on' if enabled.value else 'off'}**.", ephemeral=True)


@action_group.command(name="delete", description="Toggle message deletion on scam detection")
@_require_manage_guild()
@app_commands.choices(enabled=[
    app_commands.Choice(name="On", value=1),
    app_commands.Choice(name="Off", value=0),
])
async def cmd_action_delete(interaction: discord.Interaction, enabled: app_commands.Choice[int]) -> None:
    db = get_db()
    config = await get_config(db, str(interaction.guild_id))
    config.actions.delete = bool(enabled.value)
    await upsert_config(db, config)
    await interaction.response.send_message(f"Delete message: **{'on' if enabled.value else 'off'}**.", ephemeral=True)


@action_group.command(name="timeout", description="Set timeout duration in minutes (0 = disabled)")
@_require_manage_guild()
async def cmd_action_timeout(interaction: discord.Interaction, minutes: int) -> None:
    if minutes < 0:
        await interaction.response.send_message("Minutes must be 0 or greater.", ephemeral=True)
        return
    db = get_db()
    config = await get_config(db, str(interaction.guild_id))
    config.actions.timeout_minutes = minutes
    await upsert_config(db, config)
    label = f"{minutes}m" if minutes > 0 else "disabled"
    await interaction.response.send_message(f"Timeout: **{label}**.", ephemeral=True)


@action_group.command(name="ban", description="Toggle ban on scam detection")
@_require_manage_guild()
@app_commands.choices(enabled=[
    app_commands.Choice(name="On", value=1),
    app_commands.Choice(name="Off", value=0),
])
async def cmd_action_ban(interaction: discord.Interaction, enabled: app_commands.Choice[int]) -> None:
    db = get_db()
    config = await get_config(db, str(interaction.guild_id))
    config.actions.ban = bool(enabled.value)
    await upsert_config(db, config)
    await interaction.response.send_message(f"Ban: **{'on' if enabled.value else 'off'}**.", ephemeral=True)


@action_group.command(name="log_clean", description="Toggle logging of non-scam images")
@_require_manage_guild()
@app_commands.choices(enabled=[
    app_commands.Choice(name="On", value=1),
    app_commands.Choice(name="Off", value=0),
])
async def cmd_action_log_clean(interaction: discord.Interaction, enabled: app_commands.Choice[int]) -> None:
    db = get_db()
    config = await get_config(db, str(interaction.guild_id))
    config.actions.log_clean = bool(enabled.value)
    await upsert_config(db, config)
    await interaction.response.send_message(f"Log clean images: **{'on' if enabled.value else 'off'}**.", ephemeral=True)


class Commands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        bot.tree.add_command(antiscam)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Commands(bot))
