# cogs/music_yt.py
import asyncio
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp

YTDL_EXECUTOR = ThreadPoolExecutor(max_workers=4)

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
}

ytdl_opts = {
    "format": "bestaudio/best",
    "quiet": True,
    "default_search": "ytsearch",
    "skip_download": True,
    "nocheckcertificate": True,
    "ignoreerrors": True,
}

@dataclass
class Track:
    title: str
    url: str
    requester: discord.Member


class GuildPlayer:
    def __init__(self, bot: commands.Bot, guild: discord.Guild):
        self.bot = bot
        self.guild = guild
        self._queue: list[Track] = []
        self.voice: discord.VoiceClient | None = None
        self.current: Track | None = None
        self.volume = 0.8
        self._play_next_lock = asyncio.Lock()

    async def connect(self, channel: discord.VoiceChannel):
        if self.voice and self.voice.is_connected():
            if self.voice.channel != channel:
                await self.voice.move_to(channel)
        else:
            self.voice = await channel.connect()

    def queue_list(self) -> list[Track]:
        return list(self._queue)

    async def play_next(self):
        # Prevent concurrent calls from double-playing
        if self._play_next_lock.locked():
            return
        async with self._play_next_lock:
            if self.voice is None or not self.voice.is_connected():
                return
            if self.voice.is_playing() or self.voice.is_paused():
                return
            if not self._queue:
                self.current = None
                return

            track = self._queue.pop(0)
            self.current = track

            source = discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(track.url, **FFMPEG_OPTIONS),
                volume=self.volume
            )

            def after(error):
                if error:
                    import logging
                    logging.getLogger("zero").error("Player error: %s", error)
                asyncio.run_coroutine_threadsafe(
                    self.play_next(),
                    self.bot.loop
                )

            self.voice.play(source, after=after)

    async def add(self, track: Track):
        self._queue.append(track)
        await self.play_next()

    async def skip(self):
        if self.voice and self.voice.is_playing():
            self.voice.stop()  # after callback fires play_next

    def pause(self):
        if self.voice and self.voice.is_playing():
            self.voice.pause()

    def resume(self):
        if self.voice and self.voice.is_paused():
            self.voice.resume()

    def set_volume(self, vol: float):
        self.volume = vol
        if self.voice and self.voice.source:
            if isinstance(self.voice.source, discord.PCMVolumeTransformer):
                self.voice.source.volume = vol

    def shuffle(self):
        import random
        random.shuffle(self._queue)

    def skipto(self, index: int) -> bool:
        """Skip to 1-based queue position. Removes everything before it."""
        if index < 1 or index > len(self._queue):
            return False
        self._queue = self._queue[index - 1:]
        if self.voice and self.voice.is_playing():
            self.voice.stop()
        return True


class MusicYT(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.players: dict[int, GuildPlayer] = {}

    def get_player(self, guild: discord.Guild) -> GuildPlayer:
        return self.players.setdefault(guild.id, GuildPlayer(self.bot, guild))

    async def yt_search(self, query: str):
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
            info = await loop.run_in_executor(
                YTDL_EXECUTOR,
                lambda: ydl.extract_info(query, download=False)
            )

        if not info:
            return None

        if "entries" in info:
            info = next((e for e in info["entries"] if e), None)
            if not info:
                return None

        return info.get("url"), info.get("title", "Unknown")

    # ── Prefix commands ──────────────────────────────────────────────────────

    @commands.command(name="p", aliases=["play"])
    async def play_prefix(self, ctx: commands.Context, *, query: str):
        if not ctx.author.voice:
            return await ctx.send("Join a voice channel first.")
        player = self.get_player(ctx.guild)
        await player.connect(ctx.author.voice.channel)
        async with ctx.typing():
            data = await self.yt_search(query)
        if not data or not data[0]:
            return await ctx.send("No results found.")
        url, title = data
        await player.add(Track(title, url, ctx.author))
        await ctx.send(f"🎵 Added **{title}**")

    @commands.command(name="skip")
    async def skip(self, ctx: commands.Context):
        player = self.get_player(ctx.guild)
        if not player.current:
            return await ctx.send("Nothing is playing.")
        await player.skip()
        await ctx.send("⏭ Skipped.")

    @commands.command(name="skipto")
    async def skipto(self, ctx: commands.Context, pos: int):
        is_premium = await self.bot.db.is_premium_guild(ctx.guild.id)
        if not is_premium:
            return await ctx.send("⭐ This is a premium feature.")
        player = self.get_player(ctx.guild)
        if not player.skipto(pos):
            return await ctx.send(f"Invalid position. Queue has {len(player.queue_list())} tracks.")
        await ctx.send(f"⏭ Skipped to position {pos}.")

    @commands.command(name="queue", aliases=["q"])
    async def queue(self, ctx: commands.Context):
        player = self.get_player(ctx.guild)
        q = player.queue_list()
        if not player.current and not q:
            return await ctx.send("Queue is empty.")
        lines = []
        if player.current:
            lines.append(f"▶ **Now:** {player.current.title}")
        for i, t in enumerate(q[:15], 1):
            lines.append(f"`{i}.` {t.title}")
        if len(q) > 15:
            lines.append(f"... and {len(q) - 15} more")
        await ctx.send("\n".join(lines))

    @commands.command(name="nowplaying", aliases=["np"])
    async def nowplaying(self, ctx: commands.Context):
        player = self.get_player(ctx.guild)
        if not player.current:
            return await ctx.send("Nothing is playing.")
        embed = discord.Embed(title="Now Playing 🎵", description=player.current.title, color=discord.Color.blurple())
        embed.set_footer(text=f"Requested by {player.current.requester.display_name}")
        await ctx.send(embed=embed)

    @commands.command(name="pause")
    async def pause(self, ctx: commands.Context):
        player = self.get_player(ctx.guild)
        player.pause()
        await ctx.send("⏸ Paused.")

    @commands.command(name="resume")
    async def resume(self, ctx: commands.Context):
        player = self.get_player(ctx.guild)
        player.resume()
        await ctx.send("▶ Resumed.")

    @commands.command(name="volume", aliases=["vol"])
    async def volume(self, ctx: commands.Context, vol: int):
        import config as cfg
        if not 0 <= vol <= cfg.MAX_VOLUME:
            return await ctx.send(f"Volume must be between 0 and {cfg.MAX_VOLUME}.")
        player = self.get_player(ctx.guild)
        player.set_volume(vol / 100)
        await ctx.send(f"🔊 Volume set to {vol}%.")

    @commands.command(name="shuffle")
    async def shuffle(self, ctx: commands.Context):
        is_premium = await self.bot.db.is_premium_guild(ctx.guild.id)
        if not is_premium:
            return await ctx.send("⭐ This is a premium feature.")
        player = self.get_player(ctx.guild)
        player.shuffle()
        await ctx.send("🔀 Queue shuffled.")

    @commands.command(name="stop", aliases=["leave", "dc"])
    async def stop(self, ctx: commands.Context):
        player = self.get_player(ctx.guild)
        if player.voice and player.voice.is_connected():
            player._queue.clear()
            player.current = None
            await player.voice.disconnect()
            player.voice = None
        await ctx.send("👋 Disconnected.")

    # ── Slash commands ────────────────────────────────────────────────────────

    @app_commands.command(name="play", description="Play a song")
    async def play_slash(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        if not interaction.user.voice:
            return await interaction.followup.send("Join a voice channel first.", ephemeral=True)
        player = self.get_player(interaction.guild)
        await player.connect(interaction.user.voice.channel)
        data = await self.yt_search(query)
        if not data or not data[0]:
            return await interaction.followup.send("No results found.", ephemeral=True)
        url, title = data
        await player.add(Track(title, url, interaction.user))
        await interaction.followup.send(f"🎵 Added **{title}**")


async def setup(bot):
    await bot.add_cog(MusicYT(bot))
