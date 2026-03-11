# cogs/music.py
import asyncio, logging, math
import discord
from discord.ext import commands
from discord import app_commands
from core.player import GuildPlayer, LoopMode, FILTERS
from core.ytdl import fetch_track, search_tracks
from core.checks import premium_or_vote

log = logging.getLogger("zero")

def fmt_dur(s: int) -> str:
    if s <= 0: return "🔴 Live"
    m, sec = divmod(s, 60)
    h, m   = divmod(m, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.players: dict[int, GuildPlayer] = {}

    def get_player(self, guild: discord.Guild) -> GuildPlayer:
        if guild.id not in self.players:
            self.players[guild.id] = GuildPlayer(self.bot, guild)
        return self.players[guild.id]

    def cog_check_voice(self, ctx: commands.Context):
        return ctx.author.voice and ctx.author.voice.channel

    # ── PLAY ─────────────────────────────────────────────────────────────────
    @commands.command(name="play", aliases=["p"])
    async def play(self, ctx: commands.Context, *, query: str):
        """Play a song by name or URL."""
        if not ctx.author.voice:
            return await ctx.send("❌ Join a voice channel first.")
        player = self.get_player(ctx.guild)
        await player.connect(ctx.author.voice.channel)
        msg = await ctx.send(f"🔎 Searching for `{query}`...")
        data = await fetch_track(query)
        if not data or not data["url"]:
            return await msg.edit(content="❌ Nothing found. Try a different query.")
        from core.player import Track
        track = Track(
            title=data["title"], url=data["url"],
            webpage_url=data["webpage_url"], duration=data["duration"],
            requester=ctx.author, thumbnail=data["thumbnail"]
        )
        player.add_to_queue(track)
        await player.start()
        if player.current and player.current.title == track.title:
            embed = discord.Embed(title="▶ Now Playing", description=f"**[{track.title}]({track.webpage_url})**", color=0x1DB954)
            embed.set_thumbnail(url=track.thumbnail)
            embed.add_field(name="Duration", value=fmt_dur(track.duration))
            embed.add_field(name="Requested by", value=ctx.author.mention)
            await msg.edit(content=None, embed=embed)
        else:
            pos = len(player.queue_list())
            embed = discord.Embed(title="🎵 Added to Queue", description=f"**[{track.title}]({track.webpage_url})**", color=0x5865F2)
            embed.add_field(name="Position", value=f"#{pos}")
            embed.add_field(name="Duration", value=fmt_dur(track.duration))
            await msg.edit(content=None, embed=embed)

    # ── SEARCH ────────────────────────────────────────────────────────────────
    @commands.command(name="search", aliases=["find"])
    async def search(self, ctx: commands.Context, *, query: str):
        """Search YouTube and pick a result."""
        if not ctx.author.voice:
            return await ctx.send("❌ Join a voice channel first.")
        msg = await ctx.send(f"🔎 Searching `{query}`...")
        results = await search_tracks(query, limit=5)
        if not results:
            return await msg.edit(content="❌ No results found.")

        desc = "\n".join(
            f"`{i}.` **{r['title']}** `[{fmt_dur(r['duration'])}]`"
            for i, r in enumerate(results, 1)
        )
        embed = discord.Embed(
            title="🔎 Search Results",
            description=desc + "\n\nType a number `1-5` to pick, or `cancel`.",
            color=0x5865F2
        )
        await msg.edit(content=None, embed=embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            reply = await self.bot.wait_for("message", timeout=30.0, check=check)
        except asyncio.TimeoutError:
            return await msg.edit(embed=discord.Embed(description="⏱ Timed out.", color=0xff0000))

        if reply.content.lower() == "cancel":
            return await msg.edit(embed=discord.Embed(description="❌ Cancelled.", color=0xff0000))

        try:
            choice = int(reply.content.strip())
            assert 1 <= choice <= len(results)
        except Exception:
            return await msg.edit(embed=discord.Embed(description="❌ Invalid choice.", color=0xff0000))

        chosen = results[choice - 1]
        # Fetch full info
        data = await fetch_track(chosen["webpage_url"] or chosen["url"])
        if not data:
            return await msg.edit(content="❌ Failed to load track.")

        from core.player import Track
        player = self.get_player(ctx.guild)
        await player.connect(ctx.author.voice.channel)
        track = Track(
            title=data["title"], url=data["url"],
            webpage_url=data["webpage_url"], duration=data["duration"],
            requester=ctx.author, thumbnail=data["thumbnail"]
        )
        player.add_to_queue(track)
        await player.start()
        embed2 = discord.Embed(title="🎵 Added to Queue", description=f"**[{track.title}]({track.webpage_url})**", color=0x1DB954)
        embed2.set_thumbnail(url=track.thumbnail)
        await msg.edit(embed=embed2)

    # ── SKIP ─────────────────────────────────────────────────────────────────
    @commands.command(name="skip", aliases=["s", "next"])
    async def skip(self, ctx: commands.Context):
        """Skip the current track."""
        player = self.get_player(ctx.guild)
        if not player.current:
            return await ctx.send("❌ Nothing is playing.")
        player.skip()
        await ctx.send("⏭ Skipped.")

    # ── SKIPTO ────────────────────────────────────────────────────────────────
    @commands.command(name="skipto", aliases=["st"])
    async def skipto(self, ctx: commands.Context, pos: int):
        """Skip to a position in the queue. (Premium)"""
        if not await premium_or_vote(ctx, allow_vote=True):
            return
        player = self.get_player(ctx.guild)
        if not player.skipto(pos):
            return await ctx.send(f"❌ Invalid position. Queue has `{len(player.queue_list())}` tracks.")
        await ctx.send(f"⏭ Skipped to position **#{pos}**.")

    # ── STOP ─────────────────────────────────────────────────────────────────
    @commands.command(name="stop", aliases=["leave", "dc", "disconnect"])
    async def stop(self, ctx: commands.Context):
        """Stop music and disconnect."""
        player = self.get_player(ctx.guild)
        await player.disconnect()
        self.players.pop(ctx.guild.id, None)
        await ctx.send("👋 Disconnected and cleared the queue.")

    # ── PAUSE / RESUME ────────────────────────────────────────────────────────
    @commands.command(name="pause")
    async def pause(self, ctx: commands.Context):
        """Pause playback."""
        player = self.get_player(ctx.guild)
        player.pause()
        await ctx.send("⏸ Paused.")

    @commands.command(name="resume", aliases=["unpause", "r"])
    async def resume(self, ctx: commands.Context):
        """Resume playback."""
        player = self.get_player(ctx.guild)
        player.resume()
        await ctx.send("▶ Resumed.")

    # ── NOWPLAYING ────────────────────────────────────────────────────────────
    @commands.command(name="nowplaying", aliases=["np", "current"])
    async def nowplaying(self, ctx: commands.Context):
        """Show the current track."""
        player = self.get_player(ctx.guild)
        if not player.current:
            return await ctx.send("❌ Nothing is playing right now.")
        t = player.current
        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"**[{t.title}]({t.webpage_url})**",
            color=0x1DB954
        )
        embed.set_thumbnail(url=t.thumbnail)
        embed.add_field(name="Duration",     value=fmt_dur(t.duration))
        embed.add_field(name="Requested by", value=t.requester.mention)
        embed.add_field(name="Loop",         value=player.loop)
        embed.add_field(name="Volume",       value=f"{int(player.volume*100)}%")
        await ctx.send(embed=embed)

    # ── QUEUE ─────────────────────────────────────────────────────────────────
    @commands.command(name="queue", aliases=["q", "list"])
    async def queue(self, ctx: commands.Context, page: int = 1):
        """Show the queue."""
        player = self.get_player(ctx.guild)
        q = player.queue_list()
        if not player.current and not q:
            return await ctx.send("📭 The queue is empty.")

        per_page = 10
        pages = max(1, math.ceil(len(q) / per_page))
        page = max(1, min(page, pages))
        start = (page - 1) * per_page

        embed = discord.Embed(title=f"📋 Queue — Page {page}/{pages}", color=0x5865F2)
        if player.current:
            embed.add_field(
                name="▶ Now Playing",
                value=f"**[{player.current.title}]({player.current.webpage_url})** `[{fmt_dur(player.current.duration)}]`",
                inline=False
            )
        if q:
            chunk = q[start:start + per_page]
            lines = "\n".join(
                f"`{start+i+1}.` [{t.title}]({t.webpage_url}) `[{fmt_dur(t.duration)}]`"
                for i, t in enumerate(chunk)
            )
            embed.add_field(name="Up Next", value=lines, inline=False)
        embed.set_footer(text=f"{len(q)} tracks in queue | Loop: {player.loop}")
        await ctx.send(embed=embed)

    # ── REMOVE ────────────────────────────────────────────────────────────────
    @commands.command(name="remove", aliases=["rm"])
    async def remove(self, ctx: commands.Context, pos: int):
        """Remove a track from the queue by position."""
        player = self.get_player(ctx.guild)
        removed = player.remove(pos - 1)
        if removed is None:
            return await ctx.send("❌ Invalid position.")
        await ctx.send(f"🗑 Removed **{removed.title}**.")

    # ── MOVE ─────────────────────────────────────────────────────────────────
    @commands.command(name="move", aliases=["mv"])
    async def move(self, ctx: commands.Context, frm: int, to: int):
        """Move a track from one position to another."""
        player = self.get_player(ctx.guild)
        if not player.move(frm - 1, to - 1):
            return await ctx.send("❌ Invalid positions.")
        await ctx.send(f"✅ Moved track from **#{frm}** to **#{to}**.")

    # ── CLEAR ─────────────────────────────────────────────────────────────────
    @commands.command(name="clear", aliases=["clearqueue", "cq"])
    async def clear(self, ctx: commands.Context):
        """Clear the queue (keeps current track playing)."""
        player = self.get_player(ctx.guild)
        player.clear_queue()
        await ctx.send("🗑 Queue cleared.")

    # ── SHUFFLE ───────────────────────────────────────────────────────────────
    @commands.command(name="shuffle", aliases=["mix"])
    async def shuffle(self, ctx: commands.Context):
        """Shuffle the queue. (Premium)"""
        if not await premium_or_vote(ctx, allow_vote=True):
            return
        player = self.get_player(ctx.guild)
        if len(player.queue_list()) < 2:
            return await ctx.send("❌ Need at least 2 songs in queue to shuffle.")
        player.shuffle()
        await ctx.send("🔀 Queue shuffled!")

    # ── LOOP ─────────────────────────────────────────────────────────────────
    @commands.command(name="loop", aliases=["repeat", "lp"])
    async def loop(self, ctx: commands.Context, mode: str = None):
        """Set loop mode: off / track / queue. Queue mode is Premium."""
        player = self.get_player(ctx.guild)
        modes = [LoopMode.OFF, LoopMode.TRACK, LoopMode.QUEUE]
        if mode is None:
            # Cycle through
            idx = modes.index(player.loop) if player.loop in modes else 0
            mode = modes[(idx + 1) % len(modes)]
        else:
            mode = mode.lower()
        if mode not in modes:
            return await ctx.send("❌ Valid modes: `off`, `track`, `queue`.")
        if mode == LoopMode.QUEUE and not await premium_or_vote(ctx, allow_vote=True):
            return
        player.loop = mode
        icons = {"off": "➡️", "track": "🔂", "queue": "🔁"}
        await ctx.send(f"{icons[mode]} Loop set to **{mode}**.")

    # ── VOLUME ────────────────────────────────────────────────────────────────
    @commands.command(name="volume", aliases=["vol", "v"])
    async def volume(self, ctx: commands.Context, vol: int):
        """Set volume (0-200)."""
        import config
        if not 0 <= vol <= config.MAX_VOLUME:
            return await ctx.send(f"❌ Volume must be between **0** and **{config.MAX_VOLUME}**.")
        player = self.get_player(ctx.guild)
        player.set_volume(vol / 100)
        bar = "█" * (vol // 10) + "░" * (20 - vol // 10)
        await ctx.send(f"🔊 `{bar}` **{vol}%**")

    # ── FILTER ───────────────────────────────────────────────────────────────
    @commands.command(name="filter", aliases=["fx", "effect"])
    async def filter(self, ctx: commands.Context, name: str = None):
        """Apply an audio filter. (Premium)\nFilters: bassboost, nightcore, vaporwave, earrape, reset"""
        if not await premium_or_vote(ctx, allow_vote=True):
            return
        if name is None:
            opts = ", ".join(f"`{f}`" for f in FILTERS)
            return await ctx.send(f"🎛 Available filters: {opts}")
        name = name.lower()
        player = self.get_player(ctx.guild)
        if not player.set_filter(name):
            return await ctx.send(f"❌ Unknown filter `{name}`. Available: {', '.join(FILTERS)}")
        label = "removed" if name == "reset" else f"set to **{name}**"
        await ctx.send(f"🎛 Filter {label}.")

    # ── 247 ──────────────────────────────────────────────────────────────────
    @commands.command(name="247")
    async def mode247(self, ctx: commands.Context, arg: str = None):
        """Toggle 24/7 mode — bot stays in VC. (Premium)"""
        if not await premium_or_vote(ctx, allow_vote=False):
            return
        if arg is None:
            status = await self.bot.db.get_247(ctx.guild.id)
            return await ctx.send(f"24/7 mode is {'✅ enabled' if status else '❌ disabled'}.")
        if arg.lower() in ("on", "enable", "true", "1"):
            await self.bot.db.set_247(ctx.guild.id, True)
            await ctx.send("✅ 24/7 mode **enabled**. I'll stay in VC.")
        elif arg.lower() in ("off", "disable", "false", "0"):
            await self.bot.db.set_247(ctx.guild.id, False)
            await ctx.send("✅ 24/7 mode **disabled**.")
        else:
            await ctx.send("Usage: `.247 on` or `.247 off`")

    # ── SLASH: PLAY ───────────────────────────────────────────────────────────
    @app_commands.command(name="play", description="Play a song by name or URL")
    async def play_slash(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        if not interaction.user.voice:
            return await interaction.followup.send("❌ Join a voice channel first.", ephemeral=True)
        player = self.get_player(interaction.guild)
        await player.connect(interaction.user.voice.channel)
        data = await fetch_track(query)
        if not data:
            return await interaction.followup.send("❌ Nothing found.", ephemeral=True)
        from core.player import Track
        track = Track(
            title=data["title"], url=data["url"],
            webpage_url=data["webpage_url"], duration=data["duration"],
            requester=interaction.user, thumbnail=data["thumbnail"]
        )
        player.add_to_queue(track)
        await player.start()
        embed = discord.Embed(title="🎵 Added to Queue", description=f"**[{track.title}]({track.webpage_url})**", color=0x5865F2)
        embed.set_thumbnail(url=track.thumbnail)
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Music(bot))
