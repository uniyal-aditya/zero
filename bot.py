# bot.py
import os
import asyncio
import logging
from typing import List

import discord

# Safe opus loading - works cross-platform
if not discord.opus.is_loaded():
    try:
        discord.opus.load_opus("libopus.so.0")
    except Exception:
        try:
            discord.opus.load_opus("libopus.so")
        except Exception:
            pass  # On some systems (Windows), opus is bundled with PyNaCl

from discord.ext import commands
from dotenv import load_dotenv

import config
from core.db import Database

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("zero")

TOKEN = os.getenv("DISCORD_TOKEN")
APP_ID_RAW = os.getenv("APPLICATION_ID")
try:
    APPLICATION_ID = int(APP_ID_RAW) if APP_ID_RAW else None
except Exception:
    APPLICATION_ID = None

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix=config.PREFIX, intents=intents, application_id=APPLICATION_ID, help_command=None)
bot.db = Database()

EXTENSIONS: List[str] = [
    "cogs.music_yt",
    "cogs.help",
    "cogs.liked",
    "cogs.lyrics",
    "cogs.playlist",
    "cogs.mode247",
    "cogs.premium",
]

async def load_extensions():
    for ext in EXTENSIONS:
        try:
            await bot.load_extension(ext)
            log.info("Loaded extension: %s", ext)
        except Exception as e:
            log.exception("Failed to load %s: %s", ext, e)

@bot.event
async def on_ready():
    log.info("%s is online as %s (ID: %s)", config.BOT_NAME, bot.user, bot.user.id)
    try:
        await bot.db.init()
        log.info("Database initialized.")
    except Exception:
        log.exception("DB init failed")
    try:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"music | {config.PREFIX}help"))
    except Exception:
        log.exception("Failed to set presence")

    TEST_GUILD = os.getenv("TEST_GUILD_ID")
    try:
        if TEST_GUILD:
            guild_obj = discord.Object(id=int(TEST_GUILD))
            bot.tree.copy_global_to(guild=guild_obj)
            await bot.tree.sync(guild=guild_obj)
            log.info("Synced commands to test guild %s", TEST_GUILD)
        else:
            await bot.tree.sync()
            log.info("Slash commands synced globally (may take up to an hour to appear).")
    except Exception:
        log.exception("Slash sync failed")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    await bot.process_commands(message)

async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
