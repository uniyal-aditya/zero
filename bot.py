# bot.py
import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
import wavelink

import config
from core.db import Database

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
APP_ID = os.getenv("APPLICATION_ID")

LAVA_HOST = os.getenv("LAVALINK_HOST", config.LAVALINK_HOST)
LAVA_PORT = int(os.getenv("LAVALINK_PORT", config.LAVALINK_PORT))
LAVA_PASS = os.getenv("LAVALINK_PASSWORD", config.LAVALINK_PASSWORD)

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(
    command_prefix=config.PREFIX,
    intents=intents,
    application_id=APP_ID,
    help_command=None
)

bot.db = Database()

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
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"music | {config.PREFIX}help"))

    # Sync slash commands
    try:
        await bot.tree.sync()
        print("Slash commands synced.")
    except Exception as e:
        print("Slash sync failed:", e)

@bot.event
async def on_wavelink_node_ready(node: wavelink.Node):
    print(f"Lavalink node ready: {node.identifier}")

# important: process prefix commands when message received
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    await bot.process_commands(message)

# handle track end in a way compatible with wavelink 1.3.x
@bot.event
async def on_wavelink_track_end(player, track, reason):
    # if player has do_next method, call it
    try:
        if hasattr(player, "do_next"):
            await player.do_next()
    except Exception as e:
        print("Error in track end handling:", e)

async def load_extensions():
    extensions = [
        "cogs.music",
        "cogs.help",
        "cogs.liked",
        "cogs.lyrics",
        "cogs.mode247",
        "cogs.playlist",
    ]
    for ext in extensions:
        try:
            await bot.load_extension(ext)
            print(f"Loaded {ext}")
        except Exception as e:
            print(f"Failed to load {ext}: {e}")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
