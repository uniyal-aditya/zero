# bot.py
import os
import asyncio
import logging
from typing import List, Optional

import discord
from discord.ext import commands
from dotenv import load_dotenv
import wavelink

import config
from core.db import Database

load_dotenv()
log = logging.getLogger("zero")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

TOKEN = os.getenv("DISCORD_TOKEN")
APP_ID_RAW = os.getenv("APPLICATION_ID")
try:
    APPLICATION_ID = int(APP_ID_RAW) if APP_ID_RAW else None
except Exception:
    APPLICATION_ID = None

LAVA_HOST = os.getenv("LAVALINK_HOST", config.LAVALINK_HOST)
LAVA_PORT = int(os.getenv("LAVALINK_PORT", config.LAVALINK_PORT))
LAVA_PASS = os.getenv("LAVALINK_PASSWORD", config.LAVALINK_PASSWORD)

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(
    command_prefix=config.PREFIX,
    intents=intents,
    application_id=APPLICATION_ID,
    help_command=None
)

bot.db = Database()

EXTENSIONS: List[str] = [
    "cogs.music",
    "cogs.help",
    "cogs.liked",
    "cogs.lyrics",
    "cogs.mode247",
    "cogs.playlist",
    "cogs.premium",
]

async def create_lavalink_node_once():
    if wavelink.NodePool.nodes:
        log.info("Lavalink node already exists.")
        return
    try:
        await wavelink.NodePool.create_node(
            bot=bot,
            host=LAVA_HOST,
            port=LAVA_PORT,
            password=LAVA_PASS,
            https=False
        )
        log.info("Lavalink node created.")
    except Exception as e:
        log.exception("Failed to create lavalink node: %s", e)

async def load_extensions():
    for ext in EXTENSIONS:
        try:
            await bot.load_extension(ext)
            log.info("Loaded extension: %s", ext)
        except Exception as e:
            log.exception("Failed to load %s: %s", ext, e)

@bot.event
async def on_ready():
    log.info("%s is online as %s", config.BOT_NAME, bot.user)
    # init DB
    try:
        await bot.db.init()
    except Exception:
        log.exception("DB init failed")

    # lavalink
    await create_lavalink_node_once()

    # set presence
    try:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"music | {config.PREFIX}help"))
    except Exception:
        log.exception("Failed to set presence")

    # sync slash commands — run once
    try:
        await bot.tree.sync()
        log.info("Slash commands synced.")
    except Exception as e:
        log.exception("Slash sync failed: %s", e)

@bot.event
async def on_wavelink_node_ready(node: wavelink.Node):
    log.info("Wavelink node ready: %s", getattr(node, "identifier", "unknown"))

@bot.event
async def on_wavelink_track_end(player, track, reason):
    # delegate to player.do_next if implemented
    try:
        if hasattr(player, "do_next"):
            await player.do_next()
    except Exception:
        log.exception("Error in track end handler")

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
