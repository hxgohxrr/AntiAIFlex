import asyncio
import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from db.client import get_db

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

COGS = ["cogs.scanner", "cogs.commands"]


class AntiScamBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        for cog in COGS:
            await self.load_extension(cog)
        await self.tree.sync()
        logging.info("Slash commands synced.")

    async def on_ready(self) -> None:
        logging.info("AntiScamBot ready. Logged in as %s (ID: %s)", self.user, self.user.id)


async def main() -> None:
    token = os.environ["DISCORD_TOKEN"]
    bot = AntiScamBot()
    async with bot:
        await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
