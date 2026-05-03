import logging
import os

import discord
from discord.ext import commands

from config.defaults import MAX_IMAGE_SIZE_BYTES
from db.client import get_db
from db.guild_config import get_config
from models import GuildConfig
from services.actions import execute_actions
from services.analyzer import analyze_image
from services.logger import log_result

logger = logging.getLogger(__name__)


def should_scan(message: discord.Message, config: GuildConfig) -> bool:
    if not message.attachments:
        return False
    has_image = any(
        a.content_type
        and a.content_type.startswith("image/")
        and "gif" not in a.content_type.lower()
        for a in message.attachments
    )
    if not has_image:
        return False
    if config.scan_mode == "all_images":
        return True
    return message.content.lower().startswith("bro")


class Scanner(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api_key = os.environ["NVIDIA_API_KEY"]
        self._processing: set[int] = set()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        if message.guild is None:
            return

        if message.id in self._processing:
            logger.debug("Skipping duplicate on_message for message %d", message.id)
            return
        self._processing.add(message.id)

        try:
            await self._handle_message(message)
        finally:
            self._processing.discard(message.id)

    async def _handle_message(self, message: discord.Message) -> None:
        db = get_db()
        config = await get_config(db, str(message.guild.id))

        if config.log_channel_id is None:
            return

        if not should_scan(message, config):
            return

        image_attachment = next(
            (
                a for a in message.attachments
                if a.content_type
                and a.content_type.startswith("image/")
                and "gif" not in a.content_type.lower()
            ),
            None,
        )
        if image_attachment is None:
            return

        if image_attachment.size > MAX_IMAGE_SIZE_BYTES:
            logger.info("Skipping oversized image (%d bytes) in guild %s", image_attachment.size, message.guild.id)
            return

        try:
            image_bytes = await image_attachment.read()
        except Exception as exc:
            logger.error("Failed to read attachment: %s", exc)
            return

        result = await analyze_image(image_bytes, self.api_key)

        actions_taken: list[str] = []
        if result.is_scam and result.confidence >= config.confidence_threshold:
            actions_taken = await execute_actions(message, result, config)

        await log_result(self.bot, message, result, actions_taken, config)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Scanner(bot))
