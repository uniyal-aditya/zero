import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
import wavelink

import config
from core.db import Database

# ======================
# LOAD ENV
# ======================
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
APP_ID = os.getenv("APPLICATION_ID")

LAVA_HOST = os.getenv("LAVALINK_HOST")
LAVA_PORT = int(os.getenv("LAVALINK_PORT"))
LAVA_PASS = os.getenv("LAVALINK_PASSWORD")

# ======================
# INTENTS
# ======================
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

# ======================
# BOT INSTANCE (ONLY ONE)
# ======================
bot = commands.Bot(
    command_prefix=".",
    intents=intents,
    application_id=APP_ID,
    help_command=None
)

bot.db = Database()

# ======================
# EVENTS
# ======================
@bot.event
async def on_ready():
    print(f"{config.BOT_NAME} is online as {bot.user} (ID: {bot.user.id})")

    # Init database
    await bot.db.init()

    # Lavalink
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

    # Sync slash commands
    await bot.tree.sync()
    print("Slash commands synced.")
    print("Zero™ is fully ready.")

@bot.event
async def on_wavelink_node_ready(node: wavelink.Node):
    print(f"Lavalink node ready: {node.identifier}")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # VERY IMPORTANT: allow prefix & hybrid commands to work
    await bot.process_commands(message)


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
