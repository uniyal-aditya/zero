# bot.py
"""
Zero™ - Main bot launcher
- Robust startup and extension loading
- Lavalink (wavelink) node creation (single)
- Slash command sync done once after ready
- Prefix command support via on_message -> process_commands
- Graceful shutdown and logging
"""

import os
import asyncio
import logging
import signal
from typing import List, Optional

import discord
from discord.ext import commands
from dotenv import load_dotenv
import wavelink

import config
from core.db import Database

# -------------------------
# Logging setup
# -------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("zero")

# -------------------------
# Environment / config
# -------------------------
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
APP_ID_RAW = os.getenv("APPLICATION_ID", None)
try:
    APPLICATION_ID: Optional[int] = int(APP_ID_RAW) if APP_ID_RAW else None
except Exception:
    APPLICATION_ID = None

LAVA_HOST = os.getenv("LAVALINK_HOST", config.LAVALINK_HOST)
LAVA_PORT = int(os.getenv("LAVALINK_PORT", config.LAVALINK_PORT))
LAVA_PASS = os.getenv("LAVALINK_PASSWORD", config.LAVALINK_PASSWORD)

# -------------------------
# Intents and Bot
# -------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(
    command_prefix=config.PREFIX,
    intents=intents,
    application_id=APPLICATION_ID,
    help_command=None,
)

# attach database instance
bot.db = Database()

# internal state flags
bot._extensions_loaded = False
bot._slash_synced = False
bot._shutdown_requested = False

# -------------------------
# Utility: Extensions list
# -------------------------
EXTENSIONS: List[str] = [
    "cogs.music",
    "cogs.help",
    "cogs.liked",
    "cogs.lyrics",
    "cogs.mode247",
    "cogs.playlist",
    "cogs.premium",
]

# -------------------------
# Low-level helpers
# -------------------------
async def create_lavalink_node_once():
    """
    Create Lavalink node only if none exists. Safe to call multiple times.
    """
    if wavelink.NodePool.nodes:
        log.info("Lavalink node already present; skipping creation.")
        return

    try:
        log.info("Creating Lavalink node...")
        await wavelink.NodePool.create_node(
            bot=bot,
            host=LAVA_HOST,
            port=LAVA_PORT,
            password=LAVA_PASS,
            https=False,
        )
        log.info("Lavalink node connected.")
    except Exception as e:
        log.exception("Failed to create Lavalink node on first try: %s", e)
        # attempt one retry after short sleep
        await asyncio.sleep(2)
        try:
            await wavelink.NodePool.create_node(
                bot=bot,
                host=LAVA_HOST,
                port=LAVA_PORT,
                password=LAVA_PASS,
                https=False,
            )
            log.info("Lavalink node connected on retry.")
        except Exception as e2:
            log.exception("Lavalink node creation retry failed: %s", e2)
            # don't crash the whole bot; the bot can still run and we can try to create node later
            return

async def load_extensions():
    """
    Load all extensions in EXTENSIONS.
    This function can be called before bot.start() inside 'async with bot' as done below.
    """
    if bot._extensions_loaded:
        log.info("Extensions already loaded; skipping.")
        return

    for ext in EXTENSIONS:
        try:
            await bot.load_extension(ext)
            log.info("Loaded extension: %s", ext)
        except Exception as exc:
            log.exception("Failed loading extension %s: %s", ext, exc)
    bot._extensions_loaded = True

# -------------------------
# Events
# -------------------------
@bot.event
async def on_ready():
    """
    Called once bot is connected and ready.
    We initialize DB, ensure Lavalink node, and sync slash commands (only once).
    """
    log.info("%s is online as %s (id=%s)", config.BOT_NAME, bot.user, bot.user.id)

    # initialize database (safe to call many times)
    try:
        await bot.db.init()
        log.info("Database initialized.")
    except Exception:
        log.exception("Database initialization failed.")

    # Create Lavalink node if not present
    await create_lavalink_node_once()

    # set presence
    try:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening,
                                                            name=f"music | {config.PREFIX}help"))
    except Exception:
        log.exception("Failed to change presence.")

    # sync slash commands only once after ready and after extensions are loaded
    if not bot._slash_synced:
        try:
            # sync global commands; for large bots you might prefer guild sync during development
            await bot.tree.sync()
            bot._slash_synced = True
            log.info("Slash commands synced globally.")
        except Exception as e:
            log.exception("Failed to sync slash commands: %s", e)

@bot.event
async def on_wavelink_node_ready(node: wavelink.Node):
    log.info("Wavelink node ready: %s", getattr(node, "identifier", "unknown"))

@bot.event
async def on_wavelink_track_end(player, track, reason):
    """
    Called when a track ends. Delegate to player.do_next() if available.
    Signature compatible with recent wavelink versions.
    """
    try:
        if hasattr(player, "do_next"):
            # do_next is expected to be an async function on our MusicPlayer
            await player.do_next()
            return
    except Exception:
        log.exception("Error handling track end in player.do_next()")
    # fallback: nothing to do

@bot.event
async def on_message(message: discord.Message):
    """
    Process prefix commands while allowing other message listeners to run.
    """
    # ignore bots
    if message.author.bot:
        return
    try:
        await bot.process_commands(message)
    except Exception:
        log.exception("Error while processing commands for message: %s", message.id)

# -------------------------
# Graceful shutdown handlers
# -------------------------
async def _shutdown():
    if bot._shutdown_requested:
        return
    bot._shutdown_requested = True
    log.info("Shutdown requested: sending disconnect to Lavalink nodes and closing bot.")

    # try disconnecting voice clients gracefully
    try:
        for guild in bot.guilds:
            vc = guild.voice_client
            if vc:
                try:
                    if hasattr(vc, "queue"):
                        vc.queue.clear()
                    await vc.stop()
                    await vc.disconnect(force=True)
                except Exception:
                    # ignore per-guild failures
                    pass
    except Exception:
        log.exception("Error while cleaning up voice clients.")

    try:
        await bot.close()
        log.info("Bot closed cleanly.")
    except Exception:
        log.exception("Error while closing bot.")

def _signal_handler():
    log.info("SIGTERM/SIGINT received, scheduling shutdown...")
    asyncio.create_task(_shutdown())

# Register signal handlers for graceful shutdown in unix-like environments
try:
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGTERM, _signal_handler)
    loop.add_signal_handler(signal.SIGINT, _signal_handler)
except Exception:
    # Some platforms (Windows) or contexts may not support add_signal_handler
    pass

# -------------------------
# Main entrypoint
# -------------------------
async def _run():
    # Load extensions before start; they will be registered to bot
    await load_extensions()

    # Start the bot
    try:
        await bot.start(TOKEN)
    except Exception as e:
        log.exception("Bot.start() raised an exception: %s", e)
        # ensure clean close
        try:
            await bot.close()
        except Exception:
            pass

if __name__ == "__main__":
    try:
        log.info("Starting Zero™ bot.")
        asyncio.run(_run())
    except KeyboardInterrupt:
        log.info("Keyboard interrupt - exiting.")
    except Exception:
        log.exception("Unhandled exception in main loop.")
