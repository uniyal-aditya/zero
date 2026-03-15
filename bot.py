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
            help_command=None,   # we have our own
            case_insensitive=True,
        )

    async def setup_hook(self):
        # Load all cogs
        for cog in COGS:
            try:
                await self.load_extension(cog)
                print(f"  [✓] Loaded {cog}")
            except Exception as e:
                print(f"  [✗] Failed {cog}: {e}")

        # Connect to Lavalink
        nodes = [
            wavelink.Node(
                uri=f"http://{cfg.LAVALINK_HOST}:{cfg.LAVALINK_PORT}",
                password=cfg.LAVALINK_PASSWORD,
            )
        ]
        await wavelink.Pool.connect(nodes=nodes, client=self, cache_capacity=100)

        # Sync slash commands
        await self.tree.sync()
        print("  [✓] Slash commands synced")

    async def on_ready(self):
        print(f"""
  ██████╗ ███████╗██████╗  ██████╗
  ╚════██╗██╔════╝██╔══██╗██╔═══██╗
   █████╔╝█████╗  ██████╔╝██║   ██║
   ╚═══██╗██╔══╝  ██╔══██╗██║   ██║
  ██████╔╝███████╗██║  ██║╚██████╔╝
  ╚═════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝
  Zero Music Bot — Made by Aditya</>
  ────────────────────────────────────
  User   : {self.user}
  Guilds : {len(self.guilds)}
  Ping   : {round(self.latency * 1000)}ms
  ────────────────────────────────────
        """)
        await self.change_presence(
            activity=discord.Activity(type=discord.ActivityType.listening, name="-help | Zero Music")
        )

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        # @mention with no other content → send about embed
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
        else:
            print(f"[Unhandled Error] {ctx.command}: {error}")

    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload):
        print(f"  [✓] Lavalink node ready: {payload.node.uri}")

    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        player = payload.player
        if not player or not hasattr(player, "home"):
            return
        from utils.embeds import now_playing
        await player.home.send(embed=now_playing(player))

    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        player = payload.player
        if not player:
            return
        # Autoplay
        if getattr(player, "autoplay_on", False) and player.queue.is_empty:
            if payload.track:
                try:
                    recs = await wavelink.Pool.fetch_tracks(f"ytsearch:{payload.track.title} {payload.track.author}")
                    if recs:
                        await player.queue.put_wait(recs[1] if len(recs) > 1 else recs[0])
                except Exception:
                    pass

    async def on_wavelink_inactive_player(self, player: wavelink.Player):
        settings = __import__("utils.database", fromlist=["get_settings"]).get_settings(player.guild.id)
        if settings.get("tf_seven"):
            return  # 24/7 mode, stay connected
        await player.disconnect()


async def main():
    bot = Zero()
    async with bot:
        await bot.start(cfg.TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
