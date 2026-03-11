# bot.py
import os, asyncio, logging, time
from typing import List

import discord
from discord.ext import commands
from dotenv import load_dotenv

# ── Opus loading ──────────────────────────────────────────────────────────────
if not discord.opus.is_loaded():
    for lib in ("libopus.so.0", "libopus.so", "libopus.0.dylib", "libopus"):
        try:
            discord.opus.load_opus(lib)
            break
        except Exception:
            continue

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
log = logging.getLogger("zero")

import config
from core.db import Database
from keepalive import start_keepalive

TOKEN      = os.getenv("DISCORD_TOKEN")
APP_ID_RAW = os.getenv("APPLICATION_ID")
try:
    APPLICATION_ID = int(APP_ID_RAW) if APP_ID_RAW else None
except Exception:
    APPLICATION_ID = None

# ── Intents ───────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True  # REQUIRED for prefix commands
intents.voice_states    = True
intents.guilds          = True

# ── Bot ───────────────────────────────────────────────────────────────────────
bot = commands.Bot(
    command_prefix=config.PREFIX,
    intents=intents,
    application_id=APPLICATION_ID,
    help_command=None,
    case_insensitive=True,
)
bot.db         = Database(config.DB_PATH)
bot.start_time = time.time()

EXTENSIONS: List[str] = [
    "cogs.music",
    "cogs.playlist",
    "cogs.liked",
    "cogs.lyrics",
    "cogs.utility",
    "cogs.help",
]

async def load_extensions():
    for ext in EXTENSIONS:
        try:
            await bot.load_extension(ext)
            log.info("✅ Loaded: %s", ext)
        except Exception:
            log.exception("❌ Failed to load: %s", ext)

# ── Events ────────────────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    log.info("  %s is ONLINE", config.BOT_NAME)
    log.info("  User    : %s (ID: %s)", bot.user, bot.user.id)
    log.info("  Prefix  : %s", config.PREFIX)
    log.info("  Guilds  : %d", len(bot.guilds))
    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    try:
        await bot.db.init()
        log.info("Database ready.")
    except Exception:
        log.exception("DB init failed")

    try:
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name=f"music | {config.PREFIX}help"
            )
        )
    except Exception:
        log.exception("Failed to set presence")

    TEST_GUILD = os.getenv("TEST_GUILD_ID")
    try:
        if TEST_GUILD:
            guild_obj = discord.Object(id=int(TEST_GUILD))
            bot.tree.copy_global_to(guild=guild_obj)
            synced = await bot.tree.sync(guild=guild_obj)
            log.info("Synced %d slash commands to test guild %s", len(synced), TEST_GUILD)
        else:
            synced = await bot.tree.sync()
            log.info("Synced %d slash commands globally", len(synced))
    except Exception:
        log.exception("Slash sync failed")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx: commands.Context, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingRequiredArgument):
        return await ctx.send(f"❌ Missing argument: `{error.param.name}`. Use `.help` for usage.")
    if isinstance(error, commands.BadArgument):
        return await ctx.send(f"❌ Bad argument. Use `.help` for usage.")
    if isinstance(error, commands.NotOwner):
        return await ctx.send("❌ Owner-only command.")
    if isinstance(error, commands.CommandInvokeError):
        log.error("Command error in %s: %s", ctx.command, error.original)
        return await ctx.send(f"❌ An error occurred: `{error.original}`")
    log.error("Unhandled error: %s", error)

# ── 24/7 voice persistence ────────────────────────────────────────────────────
@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if member.id == bot.user.id:
        return
    # If bot is alone and 247 is off → leave after 3 min
    guild = member.guild
    vc = guild.voice_client
    if not vc or not vc.is_connected():
        return
    if len([m for m in vc.channel.members if not m.bot]) == 0:
        is_247 = await bot.db.get_247(guild.id)
        if not is_247:
            await asyncio.sleep(180)
            # Re-check
            if vc.is_connected() and len([m for m in vc.channel.members if not m.bot]) == 0:
                cog = bot.get_cog("Music")
                if cog and guild.id in cog.players:
                    await cog.players[guild.id].disconnect()
                    del cog.players[guild.id]

# ── Main ──────────────────────────────────────────────────────────────────────
async def main():
    async with bot:
        await start_keepalive()
        await load_extensions()
        if not TOKEN:
            log.error("DISCORD_TOKEN is not set! Add it to your environment variables.")
            return
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
