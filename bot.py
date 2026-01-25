# bot.py
import os
import asyncio
import logging
from typing import List

import discord
from discord.ext import commands
from dotenv import load_dotenv

import config
from core.db import Database

# ======================
# LOAD ENV & LOGGING
# ======================
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("zero")

TOKEN = os.getenv("DISCORD_TOKEN")
APP_ID_RAW = os.getenv("APPLICATION_ID")

try:
    APPLICATION_ID = int(APP_ID_RAW) if APP_ID_RAW else None
except Exception:
    APPLICATION_ID = None

# ======================
# INTENTS
# ======================
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

# ======================
# BOT INSTANCE
# ======================
bot = commands.Bot(
    command_prefix=config.PREFIX,  # "."
    intents=intents,
    application_id=APPLICATION_ID,
    help_command=None
)

# Attach database
bot.db = Database()

# ======================
# EXTENSIONS
# ======================
EXTENSIONS: List[str] = [
    "cogs.music_yt",   # yt-dlp music system
    "cogs.help",
    "cogs.liked",
    "cogs.lyrics",
    "cogs.playlist",
    "cogs.premium",
    "cogs.mode247",
]

async def load_extensions():
    for ext in EXTENSIONS:
        try:
            await bot.load_extension(ext)
            log.info("Loaded extension: %s", ext)
        except Exception as e:
            log.exception("Failed to load %s", ext)

# ======================
# EVENTS
# ======================
@bot.event
async def on_ready():
    log.info("%s is online as %s (ID: %s)", config.BOT_NAME, bot.user, bot.user.id)

    # Init DB
    try:
        await bot.db.init()
        log.info("Database initialized.")
    except Exception:
        log.exception("Database init failed")

    # Presence
    try:
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name=f"music | {config.PREFIX}help"
            )
        )
    except Exception:
        log.exception("Failed to set presence")

    # Slash command sync
    try:
        await bot.tree.sync()
        log.info("Slash commands synced.")
    except Exception:
        log.exception("Slash command sync failed")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    await bot.process_commands(message)

# ======================
# MAIN
# ======================
async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
