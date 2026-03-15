import discord
from discord.ext import commands
from discord import app_commands
import wavelink
import config as cfg
import utils.database as db
from utils.embeds import err, ok, now_playing, added_to_queue, _ms_to_str, help_main, help_category, BackView


def player(ctx) -> wavelink.Player | None:
    return ctx.guild.voice_client if ctx.guild else None


async def ensure_player(ctx: commands.Context) -> wavelink.Player | None:
    """Join VC or return existing. Sends error and returns None on failure."""
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send(embed=err("You must be in a voice channel!"))
        return None
    vc: wavelink.Player = ctx.guild.voice_client
    if not vc:
        settings = db.get_settings(ctx.guild.id)
        vc = await ctx.author.voice.channel.connect(cls=wavelink.Player, self_deaf=True)
        vc.home = ctx.channel
        vc.autoplay_on = False
        await vc.set_volume(settings.get("default_volume", 80))
    elif ctx.author.voice.channel != vc.channel:
        await ctx.send(embed=err("You must be in the **same** voice channel as me!"))
        return None
    return vc


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── PLAY ─────────────────────────────────────────────────────────────────
    @commands.hybrid_command(name="play", aliases=["p"], description="▶️ Play a song from YouTube or Spotify")
    @app_commands.describe(query="Song name, YouTube link, or Spotify link")
    async def play(self, ctx: commands.Context, *, query: str):
        await ctx.defer()
        vc = await ensure_player(ctx)
        if not vc:
            return
        try:
            tracks = await wavelink.Playable.search(query)
            if not tracks:
                return await ctx.send(embed=err("No results found for that query."))

            if isinstance(tracks, wavelink.Playlist):
                added = 0
                for t in tracks.tracks:
                    await vc.queue.put_wait(t)
                    added += 1
                if not vc.playing:
                    await vc.play(vc.queue.get())
                await ctx.send(embed=ok(f"▶️ Queued playlist **{tracks.name}** — **{added}** tracks."))
            else:
                track = tracks[0]
                if vc.playing:
                    await vc.queue.put_wait(track)
                    await ctx.send(embed=added_to_queue(track, len(vc.queue)))
                else:
                    await vc.play(track)
        except Exception as e:
            await ctx.send(embed=err(f"Error: {e}"))

    # ── PAUSE ────────────────────────────────────────────────────────────────
    @commands.hybrid_command(name="pause", description="⏸ Pause playback")
    async def pause(self, ctx: commands.Context):
        vc = player(ctx)
        if not vc or not vc.playing:
            return await ctx.send(embed=err("Nothing is playing."))
        if vc.paused:
            return await ctx.send(embed=err("Already paused. Use `/resume`."))
        await vc.pause(True)
        await ctx.send(embed=ok("⏸ Paused."))

    # ── RESUME ───────────────────────────────────────────────────────────────
    @commands.hybrid_command(name="resume", description="▶️ Resume paused music")
    async def resume(self, ctx: commands.Context):
        vc = player(ctx)
        if not vc or not vc.paused:
            return await ctx.send(embed=err("Music is not paused."))
        await vc.pause(False)
        await ctx.send(embed=ok("▶️ Resumed."))

    # ── SKIP ─────────────────────────────────────────────────────────────────
    @commands.hybrid_command(name="skip", aliases=["s"], description="⏭ Skip the current track")
    async def skip(self, ctx: commands.Context):
        vc = player(ctx)
        if not vc or not vc.playing:
            return await ctx.send(embed=err("Nothing is playing."))
        title = vc.current.title if vc.current else "track"
        await vc.skip()
        await ctx.send(embed=ok(f"⏭ Skipped **{title}**."))

    # ── BACK ─────────────────────────────────────────────────────────────────
    @commands.hybrid_command(name="back", aliases=["prev", "previous"], description="⏮ Go back to previous track")
    async def back(self, ctx: commands.Context):
        vc = player(ctx)
        if not vc:
            return await ctx.send(embed=err("I'm not in a voice channel."))
        if vc.queue.history.is_empty:
            return await ctx.send(embed=err("No previous track in history!"))
        prev = vc.queue.history[-1]
        vc.queue.history.remove(prev)
        if vc.current:
            await vc.queue.put_at(0, vc.current)
        await vc.play(prev)
        await ctx.send(embed=ok(f"⏮ Playing previous: **{prev.title}**"))

    # ── STOP ─────────────────────────────────────────────────────────────────
    @commands.hybrid_command(name="stop", description="⏹ Stop music and clear queue")
    async def stop(self, ctx: commands.Context):
        vc = player(ctx)
        if not vc:
            return await ctx.send(embed=err("I'm not in a voice channel."))
        vc.queue.clear()
        await vc.stop()
        await ctx.send(embed=ok("⏹ Stopped and cleared the queue."))

    # ── LEAVE ────────────────────────────────────────────────────────────────
    @commands.hybrid_command(name="leave", aliases=["dc", "disconnect"], description="👋 Disconnect from voice")
    async def leave(self, ctx: commands.Context):
        vc = player(ctx)
        if not vc:
            return await ctx.send(embed=err("I'm not in a voice channel."))
        await vc.disconnect()
        await ctx.send(embed=ok("👋 Disconnected."))

    # ── NOW PLAYING ───────────────────────────────────────────────────────────
    @commands.hybrid_command(name="nowplaying", aliases=["np"], description="🎵 Show currently playing track")
    async def nowplaying(self, ctx: commands.Context):
        vc = player(ctx)
        if not vc or not vc.current:
            return await ctx.send(embed=err("Nothing is playing."))
        await ctx.send(embed=now_playing(vc))

    # ── VOLUME ───────────────────────────────────────────────────────────────
    @commands.hybrid_command(name="volume", aliases=["v", "vol"], description="🔊 Set volume (1–200)")
    @app_commands.describe(level="Volume level between 1 and 200")
    async def volume(self, ctx: commands.Context, level: int):
        vc = player(ctx)
        if not vc:
            return await ctx.send(embed=err("I'm not in a voice channel."))
        if not 1 <= level <= 200:
            return await ctx.send(embed=err("Volume must be between **1** and **200**."))
        await vc.set_volume(level)
        icon = "🔇" if level == 0 else "🔈" if level < 50 else "🔉" if level < 150 else "🔊"
        await ctx.send(embed=ok(f"{icon} Volume set to **{level}%**."))

    # ── SEEK ─────────────────────────────────────────────────────────────────
    @commands.hybrid_command(name="seek", description="🎯 Seek to a timestamp (mm:ss)")
    @app_commands.describe(timestamp="Timestamp e.g. 1:30")
    async def seek(self, ctx: commands.Context, timestamp: str):
        vc = player(ctx)
        if not vc or not vc.current:
            return await ctx.send(embed=err("Nothing is playing."))
        try:
            parts = timestamp.split(":")[::-1]
            ms = (int(parts[0]) + int(parts[1])*60 + (int(parts[2]) if len(parts)>2 else 0)*3600) * 1000
        except Exception:
            return await ctx.send(embed=err("Invalid timestamp. Use `mm:ss` or `hh:mm:ss`."))
        await vc.seek(ms)
        await ctx.send(embed=ok(f"⏩ Seeked to **{timestamp}**."))

    # ── FORWARD ──────────────────────────────────────────────────────────────
    @commands.hybrid_command(name="forward", aliases=["ff"], description="⏩ Fast-forward N seconds")
    @app_commands.describe(seconds="Seconds to skip forward (default 10)")
    async def forward(self, ctx: commands.Context, seconds: int = 10):
        vc = player(ctx)
        if not vc or not vc.current:
            return await ctx.send(embed=err("Nothing is playing."))
        new_pos = min(vc.position + seconds*1000, vc.current.length - 1000)
        await vc.seek(new_pos)
        await ctx.send(embed=ok(f"⏩ Forwarded **{seconds}s**."))

    # ── REWIND ───────────────────────────────────────────────────────────────
    @commands.hybrid_command(name="rewind", aliases=["rw"], description="⏪ Rewind N seconds")
    @app_commands.describe(seconds="Seconds to rewind (default 10)")
    async def rewind(self, ctx: commands.Context, seconds: int = 10):
        vc = player(ctx)
        if not vc or not vc.current:
            return await ctx.send(embed=err("Nothing is playing."))
        new_pos = max(vc.position - seconds*1000, 0)
        await vc.seek(new_pos)
        await ctx.send(embed=ok(f"⏪ Rewound **{seconds}s**."))

    # ── LYRICS ───────────────────────────────────────────────────────────────
    @commands.hybrid_command(name="lyrics", description="🎤 Get lyrics for a song")
    @app_commands.describe(query="Song title (defaults to current track)")
    async def lyrics(self, ctx: commands.Context, *, query: str = None):
        await ctx.defer()
        vc = player(ctx)
        search = query or (vc.current.title if vc and vc.current else None)
        if not search:
            return await ctx.send(embed=err("Nothing is playing. Provide a song name."))
        try:
            import urllib.parse, aiohttp
            artist, title_part = search.split(" ", 1) if " " in search else (search, search)
            url = f"https://api.lyrics.ovh/v1/{urllib.parse.quote(search.replace(' ', '/'))}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as r:
                    if r.status != 200:
                        raise ValueError("Not found")
                    data = await r.json()
                    lyrics = data.get("lyrics", "").strip()
            if not lyrics:
                raise ValueError("Empty")
            chunks = [lyrics[i:i+3900] for i in range(0, len(lyrics), 3900)]
            for i, chunk in enumerate(chunks[:3]):
                e = discord.Embed(
                    title=f"🎤 {search}" if i == 0 else "\u200b",
                    description=chunk,
                    colour=cfg.COL_PRIMARY,
                )
                e.set_footer(text="Zero Music • Made by Aditya</>")
                await ctx.send(embed=e)
        except Exception:
            await ctx.send(embed=err(f"Lyrics not found for **{search}**."))

    # ── HELP ─────────────────────────────────────────────────────────────────
    @commands.hybrid_command(name="help", aliases=["h", "cmds", "commands"], description="📖 Show the help menu")
    @app_commands.describe(category="Category to jump to")
    @app_commands.choices(category=[
        app_commands.Choice(name="🌐 General",     value="general"),
        app_commands.Choice(name="🎵 Music",        value="music"),
        app_commands.Choice(name="📋 Queue",        value="queue"),
        app_commands.Choice(name="📁 Playlists",    value="playlist"),
        app_commands.Choice(name="❤️ Liked Songs",  value="liked"),
        app_commands.Choice(name="⭐ Premium",      value="premium"),
        app_commands.Choice(name="👑 Owner",        value="owner"),
    ])
    async def help(self, ctx: commands.Context, category: str = None):
        if category:
            embed = help_category(category.lower())
            if not embed:
                return await ctx.send(embed=err("Unknown category."))
            await ctx.send(embed=embed, view=BackView())
        else:
            embed, view = help_main(self.bot)
            await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Music(bot))
