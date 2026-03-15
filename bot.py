import asyncio
import os
import discord
from discord.ext import commands
import wavelink
import config as cfg
from utils.embeds import about, err

COGS = [
    "cogs.music",
    "cogs.queue",
    "cogs.playlist",
    "cogs.liked",
    "cogs.premium",
    "cogs.owner",
    "cogs.general",
]


class Zero(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(
            command_prefix=cfg.PREFIX,
            intents=intents,
            help_command=None,
            case_insensitive=True,
        )
        self.lavalink_connected = False

    async def setup_hook(self):
        # ── Load cogs ─────────────────────────────────────────────────────────
        for cog in COGS:
            try:
                await self.load_extension(cog)
                print(f"  [+] Loaded {cog}")
            except Exception as e:
                print(f"  [!] Failed to load {cog}: {e}")

        # ── Connect to Lavalink (non-fatal if it fails) ───────────────────────
        await self._connect_lavalink()

        # ── Sync slash commands ───────────────────────────────────────────────
        try:
            await self.tree.sync()
            print("  [+] Slash commands synced globally")
        except Exception as e:
            print(f"  [!] Slash sync failed: {e}")

    async def _connect_lavalink(self):
        port = cfg.LAVALINK_PORT
        scheme = "https" if port == 443 else "http"
        uri = f"{scheme}://{cfg.LAVALINK_HOST}:{port}"
        print(f"  [~] Connecting to Lavalink at {uri} ...")
        try:
            node = wavelink.Node(uri=uri, password=cfg.LAVALINK_PASSWORD)
            await wavelink.Pool.connect(nodes=[node], client=self, cache_capacity=100)
            self.lavalink_connected = True
            print(f"  [+] Lavalink connected!")
        except Exception as e:
            self.lavalink_connected = False
            print(f"""
  [!] Lavalink connection FAILED: {e}
  ─────────────────────────────────────────────────────
  Music commands will NOT work until Lavalink is set up.

  QUICK FIX - add these 3 lines to your .env file:
    LAVALINK_HOST=lavalink.devamop.in
    LAVALINK_PORT=443
    LAVALINK_PASSWORD=DevamOP

  Then restart the bot.
  ─────────────────────────────────────────────────────
""")

    async def on_ready(self):
        lava = "Connected" if self.lavalink_connected else "NOT connected (music wont work - check .env)"
        print(f"""
  ██████╗ ███████╗██████╗  ██████╗
  ╚════██╗██╔════╝██╔══██╗██╔═══██╗
   █████╔╝█████╗  ██████╔╝██║   ██║
   ╚═══██╗██╔══╝  ██╔══██╗██║   ██║
  ██████╔╝███████╗██║  ██║╚██████╔╝
  ╚═════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝
  Zero Music Bot - Made by Aditya</>
  ─────────────────────────────────────
  User      : {self.user}
  Guilds    : {len(self.guilds)}
  Ping      : {round(self.latency * 1000)}ms
  Lavalink  : {lava}
  ─────────────────────────────────────
""")
        self.loop.create_task(self._rotate_status())

    async def _rotate_status(self):
        statuses = [
            discord.Activity(type=discord.ActivityType.listening, name="-help | Zero Music"),
            discord.Activity(type=discord.ActivityType.watching,  name=f"{len(self.guilds)} servers"),
            discord.Activity(type=discord.ActivityType.playing,   name="top.gg | vote for premium"),
            discord.Activity(type=discord.ActivityType.listening, name="HD Music"),
        ]
        i = 0
        while not self.is_closed():
            await self.change_presence(activity=statuses[i % len(statuses)])
            i += 1
            await asyncio.sleep(30)

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if (
            self.user
            and self.user.mentioned_in(message)
            and message.content.strip() in (f"<@{self.user.id}>", f"<@!{self.user.id}>")
        ):
            await message.reply(embed=about(self, message.author.display_name), mention_author=False)
            return
        await self.process_commands(message)

    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply(embed=err(f"Missing argument: `{error.param.name}`"), mention_author=False)
        elif isinstance(error, commands.BadArgument):
            await ctx.reply(embed=err(str(error)), mention_author=False)
        elif isinstance(error, commands.CheckFailure):
            from utils.embeds import premium_wall
            if "PREMIUM_REQUIRED" in str(error):
                await ctx.reply(embed=premium_wall(), mention_author=False)
            else:
                await ctx.reply(embed=err(str(error)), mention_author=False)
        elif isinstance(error, commands.CommandInvokeError):
            orig = error.original
            if "no node" in str(orig).lower() or "wavelink" in type(orig).__module__:
                await ctx.reply(
                    embed=err(
                        "Music is unavailable — Lavalink is not connected.\n\n"
                        "Add these to your `.env` and restart:\n"
                        "```\nLAVALINK_HOST=lavalink.devamop.in\n"
                        "LAVALINK_PORT=443\n"
                        "LAVALINK_PASSWORD=DevamOP\n```"
                    ),
                    mention_author=False,
                )
            else:
                print(f"[CommandInvokeError] {ctx.command}: {orig}")
        else:
            print(f"[Error] {ctx.command}: {error}")

    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload):
        self.lavalink_connected = True
        print(f"  [+] Lavalink node ready: {payload.node.uri}")

    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        player = payload.player
        if not player or not hasattr(player, "home"):
            return
        from utils.embeds import now_playing
        try:
            await player.home.send(embed=now_playing(player))
        except Exception:
            pass

    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        player = payload.player
        if not player:
            return
        if getattr(player, "autoplay_on", False) and player.queue.is_empty:
            if payload.track:
                try:
                    results = await wavelink.Playable.search(
                        f"ytsearch:{payload.track.title} {payload.track.author}"
                    )
                    if results:
                        await player.queue.put_wait(results[1] if len(results) > 1 else results[0])
                except Exception:
                    pass

    async def on_wavelink_inactive_player(self, player: wavelink.Player):
        import utils.database as db
        settings = db.get_settings(player.guild.id)
        if settings.get("tf_seven"):
            return
        await player.disconnect()


async def main():
    bot = Zero()
    async with bot:
        await bot.start(cfg.TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
