import discord
from discord.ext import commands
from discord import app_commands
import wavelink
import config as cfg
import utils.database as db
from utils.embeds import err, ok, now_playing, progress_bar, _ms_to_str


def get_player(ctx) -> wavelink.Player | None:
    return ctx.guild.voice_client


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── HELPERS ───────────────────────────────────────────────────────────────

    async def ensure_player(self, ctx) -> wavelink.Player | None:
        """Join or return existing player. Returns None if user not in VC."""
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.reply(embed=err("You must be in a voice channel!"), mention_author=False)
            return None
        player: wavelink.Player = ctx.guild.voice_client
        if not player:
            settings = db.get_settings(ctx.guild.id)
            player = await ctx.author.voice.channel.connect(cls=wavelink.Player, self_deaf=True)
            player.home = ctx.channel
            player.autoplay_on = False
            player.volume = settings.get("default_volume", 80)
            await player.set_volume(player.volume)
        elif ctx.author.voice.channel != player.channel:
            await ctx.reply(embed=err("You must be in the **same** voice channel as me!"), mention_author=False)
            return None
        return player

    # ── PLAY ──────────────────────────────────────────────────────────────────

    @commands.command(name="play", aliases=["p"])
    async def play(self, ctx: commands.Context, *, query: str = None):
        """Play a song from YouTube or Spotify."""
        if not query:
            return await ctx.reply(embed=err("Provide a song name, YouTube or Spotify link."), mention_author=False)

        async with ctx.typing():
            player = await self.ensure_player(ctx)
            if not player:
                return

            try:
                tracks = await wavelink.Playable.search(query)
                if not tracks:
                    return await ctx.reply(embed=err("No results found for that query."), mention_author=False)

                if isinstance(tracks, wavelink.Playlist):
                    added = 0
                    for t in tracks.tracks:
                        t.extras = discord.Object(id=ctx.author.id)
                        await player.queue.put_wait(t)
                        added += 1
                    if not player.playing:
                        await player.play(player.queue.get())
                    await ctx.reply(embed=ok(f"▶️ Queued playlist **{tracks.name}** — **{added}** tracks."), mention_author=False)
                else:
                    track = tracks[0]
                    track.extras = discord.Object(id=ctx.author.id)
                    if player.playing:
                        await player.queue.put_wait(track)
                        from utils.embeds import added_to_queue
                        pos = len(player.queue)
                        await ctx.reply(embed=added_to_queue(track, pos), mention_author=False)
                    else:
                        await player.play(track)
                        # now_playing sent via on_wavelink_track_start

            except Exception as e:
                await ctx.reply(embed=err(f"Error: {e}"), mention_author=False)

    @app_commands.command(name="play", description="▶️ Play a song from YouTube or Spotify")
    @app_commands.describe(query="Song name, YouTube or Spotify URL")
    async def play_slash(self, interaction: discord.Interaction, query: str):
        ctx = await commands.Context.from_interaction(interaction)
        await self.play(ctx, query=query)

    # ── PAUSE ─────────────────────────────────────────────────────────────────

    @commands.command(name="pause")
    async def pause(self, ctx: commands.Context):
        """Pause playback."""
        player = get_player(ctx)
        if not player or not player.playing:
            return await ctx.reply(embed=err("Nothing is playing."), mention_author=False)
        if player.paused:
            return await ctx.reply(embed=err("Already paused."), mention_author=False)
        await player.pause(True)
        await ctx.reply(embed=ok("⏸ Paused."), mention_author=False)

    @app_commands.command(name="pause", description="⏸ Pause playback")
    async def pause_slash(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        await self.pause(ctx)

    # ── RESUME ────────────────────────────────────────────────────────────────

    @commands.command(name="resume")
    async def resume(self, ctx: commands.Context):
        """Resume paused music."""
        player = get_player(ctx)
        if not player or not player.paused:
            return await ctx.reply(embed=err("Music is not paused."), mention_author=False)
        await player.pause(False)
        await ctx.reply(embed=ok("▶️ Resumed."), mention_author=False)

    @app_commands.command(name="resume", description="▶️ Resume paused music")
    async def resume_slash(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        await self.resume(ctx)

    # ── SKIP ──────────────────────────────────────────────────────────────────

    @commands.command(name="skip", aliases=["s"])
    async def skip(self, ctx: commands.Context):
        """Skip the current track."""
        player = get_player(ctx)
        if not player or not player.playing:
            return await ctx.reply(embed=err("Nothing is playing."), mention_author=False)
        title = player.current.title if player.current else "track"
        await player.skip()
        await ctx.reply(embed=ok(f"⏭ Skipped **{title}**."), mention_author=False)

    @app_commands.command(name="skip", description="⏭ Skip the current track")
    async def skip_slash(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        await self.skip(ctx)

    # ── BACK ──────────────────────────────────────────────────────────────────

    @commands.command(name="back", aliases=["b", "prev", "previous"])
    async def back(self, ctx: commands.Context):
        """Go back to the previous track."""
        player = get_player(ctx)
        if not player:
            return await ctx.reply(embed=err("I'm not in a voice channel."), mention_author=False)
        if player.queue.history.is_empty:
            return await ctx.reply(embed=err("No previous track in history!"), mention_author=False)
        prev = player.queue.history[-1]
        player.queue.history.remove(prev)
        if player.current:
            await player.queue.put_at(0, player.current)
        await player.play(prev)
        await ctx.reply(embed=ok(f"⏮ Playing previous track: **{prev.title}**"), mention_author=False)

    @app_commands.command(name="back", description="⏮ Go back to the previous track")
    async def back_slash(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        await self.back(ctx)

    # ── STOP ──────────────────────────────────────────────────────────────────

    @commands.command(name="stop")
    async def stop(self, ctx: commands.Context):
        """Stop music and clear the queue."""
        player = get_player(ctx)
        if not player:
            return await ctx.reply(embed=err("I'm not in a voice channel."), mention_author=False)
        player.queue.clear()
        await player.stop()
        await ctx.reply(embed=ok("⏹ Stopped and cleared the queue."), mention_author=False)

    @app_commands.command(name="stop", description="⏹ Stop music and clear queue")
    async def stop_slash(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        await self.stop(ctx)

    # ── LEAVE ─────────────────────────────────────────────────────────────────

    @commands.command(name="leave", aliases=["dc", "disconnect"])
    async def leave(self, ctx: commands.Context):
        """Disconnect the bot."""
        player = get_player(ctx)
        if not player:
            return await ctx.reply(embed=err("I'm not in a voice channel."), mention_author=False)
        await player.disconnect()
        await ctx.reply(embed=ok("👋 Disconnected."), mention_author=False)

    @app_commands.command(name="leave", description="👋 Disconnect Zero from voice")
    async def leave_slash(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        await self.leave(ctx)

    # ── NOW PLAYING ───────────────────────────────────────────────────────────

    @commands.command(name="nowplaying", aliases=["np", "now"])
    async def nowplaying(self, ctx: commands.Context):
        """Show the currently playing track."""
        player = get_player(ctx)
        if not player or not player.current:
            return await ctx.reply(embed=err("Nothing is playing."), mention_author=False)
        await ctx.reply(embed=now_playing(player), mention_author=False)

    @app_commands.command(name="nowplaying", description="🎵 Show the currently playing track")
    async def np_slash(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        await self.nowplaying(ctx)

    # ── VOLUME ────────────────────────────────────────────────────────────────

    @commands.command(name="volume", aliases=["v", "vol"])
    async def volume(self, ctx: commands.Context, level: int = None):
        """Set volume (1–200)."""
        player = get_player(ctx)
        if not player:
            return await ctx.reply(embed=err("I'm not in a voice channel."), mention_author=False)
        if level is None:
            return await ctx.reply(embed=ok(f"🔊 Current volume: **{player.volume}%**"), mention_author=False)
        if not 1 <= level <= 200:
            return await ctx.reply(embed=err("Volume must be between **1** and **200**."), mention_author=False)
        await player.set_volume(level)
        icon = "🔇" if level == 0 else "🔈" if level < 50 else "🔉" if level < 150 else "🔊"
        await ctx.reply(embed=ok(f"{icon} Volume set to **{level}%**."), mention_author=False)

    @app_commands.command(name="volume", description="🔊 Set volume (1–200)")
    @app_commands.describe(level="Volume level 1–200")
    async def volume_slash(self, interaction: discord.Interaction, level: app_commands.Range[int, 1, 200]):
        ctx = await commands.Context.from_interaction(interaction)
        await self.volume(ctx, level)

    # ── SEEK ──────────────────────────────────────────────────────────────────

    @commands.command(name="seek")
    async def seek(self, ctx: commands.Context, timestamp: str = None):
        """Seek to a timestamp (mm:ss or hh:mm:ss)."""
        player = get_player(ctx)
        if not player or not player.current:
            return await ctx.reply(embed=err("Nothing is playing."), mention_author=False)
        if not timestamp:
            return await ctx.reply(embed=err("Provide a timestamp e.g. `1:30`"), mention_author=False)
        try:
            parts = timestamp.split(":")[::-1]
            ms = (int(parts[0]) + int(parts[1]) * 60 + (int(parts[2]) if len(parts) > 2 else 0) * 3600) * 1000
        except Exception:
            return await ctx.reply(embed=err("Invalid timestamp. Use `mm:ss` or `hh:mm:ss`."), mention_author=False)
        await player.seek(ms)
        await ctx.reply(embed=ok(f"⏩ Seeked to **{timestamp}**."), mention_author=False)

    @app_commands.command(name="seek", description="🎯 Seek to a timestamp")
    @app_commands.describe(timestamp="e.g. 1:30")
    async def seek_slash(self, interaction: discord.Interaction, timestamp: str):
        ctx = await commands.Context.from_interaction(interaction)
        await self.seek(ctx, timestamp)

    # ── FORWARD ───────────────────────────────────────────────────────────────

    @commands.command(name="forward", aliases=["ff", "fwd"])
    async def forward(self, ctx: commands.Context, seconds: int = 10):
        """Fast-forward N seconds."""
        player = get_player(ctx)
        if not player or not player.current:
            return await ctx.reply(embed=err("Nothing is playing."), mention_author=False)
        new_pos = min(player.position + seconds * 1000, player.current.length - 1000)
        await player.seek(new_pos)
        await ctx.reply(embed=ok(f"⏩ Forwarded **{seconds}s**."), mention_author=False)

    @app_commands.command(name="forward", description="⏩ Fast-forward N seconds")
    @app_commands.describe(seconds="Seconds to skip (default 10)")
    async def forward_slash(self, interaction: discord.Interaction, seconds: int = 10):
        ctx = await commands.Context.from_interaction(interaction)
        await self.forward(ctx, seconds)

    # ── REWIND ────────────────────────────────────────────────────────────────

    @commands.command(name="rewind", aliases=["rw", "rew"])
    async def rewind(self, ctx: commands.Context, seconds: int = 10):
        """Rewind N seconds."""
        player = get_player(ctx)
        if not player or not player.current:
            return await ctx.reply(embed=err("Nothing is playing."), mention_author=False)
        new_pos = max(player.position - seconds * 1000, 0)
        await player.seek(new_pos)
        await ctx.reply(embed=ok(f"⏪ Rewound **{seconds}s**."), mention_author=False)

    @app_commands.command(name="rewind", description="⏪ Rewind N seconds")
    @app_commands.describe(seconds="Seconds to rewind (default 10)")
    async def rewind_slash(self, interaction: discord.Interaction, seconds: int = 10):
        ctx = await commands.Context.from_interaction(interaction)
        await self.rewind(ctx, seconds)

    # ── LYRICS ────────────────────────────────────────────────────────────────

    @commands.command(name="lyrics")
    async def lyrics(self, ctx: commands.Context, *, query: str = None):
        """Get lyrics for a song."""
        player = get_player(ctx)
        search = query or (player.current.title if player and player.current else None)
        if not search:
            return await ctx.reply(embed=err("Nothing is playing. Provide a song name."), mention_author=False)
        async with ctx.typing():
            try:
                import urllib.parse, aiohttp
                q = urllib.parse.quote(search)
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"https://api.lyrics.ovh/v1/{q.replace('%20', '/')}",
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as r:
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
                await ctx.reply(embed=err(f"Lyrics not found for **{search}**."), mention_author=False)

    @app_commands.command(name="lyrics", description="🎤 Get lyrics for a song")
    @app_commands.describe(query="Song title (defaults to current)")
    async def lyrics_slash(self, interaction: discord.Interaction, query: str = None):
        ctx = await commands.Context.from_interaction(interaction)
        await self.lyrics(ctx, query=query)

    # ── HELP ──────────────────────────────────────────────────────────────────

    @commands.command(name="help", aliases=["h", "commands", "cmds"])
    async def help(self, ctx: commands.Context, category: str = None):
        """Show the interactive help menu."""
        from utils.embeds import help_main, help_category, BackView
        if category:
            embed = help_category(category.lower())
            if not embed:
                return await ctx.reply(embed=err("Unknown category. Try: `general` `music` `queue` `playlist` `liked` `premium` `owner`"), mention_author=False)
            await ctx.reply(embed=embed, view=BackView(), mention_author=False)
        else:
            embed, view = help_main(self.bot)
            await ctx.reply(embed=embed, view=view, mention_author=False)

    @app_commands.command(name="help", description="📖 Show the interactive help menu")
    @app_commands.describe(category="Optional category to jump to")
    @app_commands.choices(category=[
        app_commands.Choice(name="🌐 General",     value="general"),
        app_commands.Choice(name="🎵 Music",       value="music"),
        app_commands.Choice(name="📋 Queue",        value="queue"),
        app_commands.Choice(name="📁 Playlists",    value="playlist"),
        app_commands.Choice(name="❤️ Liked Songs",  value="liked"),
        app_commands.Choice(name="⭐ Premium",      value="premium"),
        app_commands.Choice(name="👑 Owner",        value="owner"),
    ])
    async def help_slash(self, interaction: discord.Interaction, category: str = None):
        ctx = await commands.Context.from_interaction(interaction)
        await self.help(ctx, category)


async def setup(bot):
    await bot.add_cog(Music(bot))
