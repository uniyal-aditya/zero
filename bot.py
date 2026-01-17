# bot.py
import os
import discord
from discord.ext import commands
import wavelink
from dotenv import load_dotenv
import asyncio
import config
from core.db import Database

# ======================
# ENV
# ======================
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
APP_ID = os.getenv("APPLICATION_ID")

LAVA_HOST = os.getenv("LAVALINK_HOST", "127.0.0.1")
LAVA_PORT = int(os.getenv("LAVALINK_PORT", 2333))
LAVA_PASS = os.getenv("LAVALINK_PASSWORD", "youshallnotpass")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing in .env")

# ======================
# BOT SETUP
# ======================
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix=config.PREFIX,
    intents=intents,
    application_id=APP_ID
)

bot.db = Database()

# ======================
# EVENTS
# ======================
@bot.event
async def on_ready():
    print(f"{config.BOT_NAME} is online as {bot.user} (ID: {bot.user.id})")

    # Init DB
    await bot.db.init()

    # Lavalink node
    if not wavelink.NodePool.nodes:
        await wavelink.NodePool.create_node(
            bot=bot,
            host=LAVA_HOST,
            port=LAVA_PORT,
            password=LAVA_PASS,
            https=False
        )
        print("Lavalink node connected.")

    # Presence
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name="music | .help"
        )
    )

    print("Zero™ is fully ready.")

@bot.event
async def on_wavelink_node_ready(node: wavelink.Node):
    print(f"Lavalink node ready: {node.identifier}")

# ======================
# TRACK END HANDLER
# ======================
@wavelink.WavelinkMixin.listener()
async def on_wavelink_track_end(payload: wavelink.TrackEndEventPayload):
    player = payload.player

    try:
        if hasattr(player, "do_next"):
            await player.do_next()
    except Exception as e:
        print("Error handling track end:", e)

# ======================
# EXTENSIONS
# ======================
async def load_extensions():
    extensions = [
        "cogs.music",
        "cogs.liked",
        "cogs.lyrics",
        "cogs.mode247",
        "cogs.help",
    ]

    for ext in extensions:
        try:
            await bot.load_extension(ext)
            print(f"Loaded {ext}")
        except Exception as e:
            print(f"Failed to load {ext}: {e}")

# ======================
# MAIN
# ======================
async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
