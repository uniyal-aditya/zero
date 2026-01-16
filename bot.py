# bot.py
import os
import discord
from discord.ext import commands
import wavelink
from dotenv import load_dotenv
import config

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
APP_ID = os.getenv("APPLICATION_ID")
LAVA_HOST = os.getenv("LAVALINK_HOST", "127.0.0.1")
LAVA_PORT = int(os.getenv("LAVALINK_PORT", 2333))
LAVA_PASS = os.getenv("LAVALINK_PASSWORD", "youshallnotpass")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents, application_id=APP_ID)

# On ready: create Lavalink node
@bot.event
async def on_ready():
    print(f"{config.BOT_NAME} is online. ({bot.user})")
    # create node if none exists
    if not wavelink.NodePool.nodes:
        await wavelink.NodePool.create_node(bot=bot,
                                           host=LAVA_HOST,
                                           port=LAVA_PORT,
                                           password=LAVA_PASS,
                                           https=False)
    # sync commands
    try:
        await bot.tree.sync()
        print("Slash commands synced.")
    except Exception as e:
        print("Failed to sync commands:", e)

# Wavelink events
@bot.event
async def on_wavelink_node_ready(node: wavelink.Node):
    print(f"Node {node.identifier} is ready.")

@bot.event
async def on_wavelink_track_end(player: wavelink.Player, track, reason):
    # custom player's do_next
    try:
        if hasattr(player, "do_next"):
            await player.do_next()
    except Exception as e:
        print("Error in track end handler:", e)

# Load cogs
async def load_extensions():
    for ext in ["cogs.music"]:
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
    import asyncio
    asyncio.run(main())
