# cogs/music_yt.py
import asyncio
import functools
import random
from dataclasses import dataclass
from typing import Optional, List, Dict

import discord
from discord.ext import commands
import yt_dlp

# ======================
# YT-DLP + FFMPEG CONFIG
# ======================
FFMPEG_BEFORE = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
FFMPEG_OPTIONS = "-vn"

YTDL_OPTS = {
    "format": "bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch",
    "skip_download": True,
}

YTDL = yt_dlp.YoutubeDL(YTDL_OPTS)

# ======================
# DATA MODELS
# ======================
@dataclass
class Track:
    title: str
    stream_url: str
    duration: int
    requester_id: int


# ======================
# GUILD PLAYER
# ======================
class GuildPlayer:
    def __init__(self, bot: commands.Bot, guild: discord.Guild):
        self.bot = bot
        self.guild = guild
        self.queue: List[Track] = []
        self.current: Optional[Track] = None
        self.voice: Optional[discord.VoiceClient] = None
        self.lock = asyncio.Lock()

        self.loop_mode = "off"  # off | track | queue
        self.volume = 0.8

    async def connect(self, channel: discord.VoiceChannel):
        if not self.voice or not self.voice.is_connected():
            self.voice = await channel.connect()

    async def play_next(self):
        async with self.lock:
            if not self.voice or self.voice.is_playing():
                return

            # Determine next track
            if self.loop_mode == "track" and self.current:
                track = self.current
            else:
                if not self.queue:
                    self.current = None
                    return
                track = self.queue.pop(0)
                if self.loop_mode == "queue":
                    self.queue.append(track)

            self.current = track

            source = discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(
                    track.stream_url,
                    before_options=FFMPEG_BEFORE,
                    options=FFMPEG_OPTIONS,
                ),
                volume=self.volume,
            )

            def after_play(err):
                if err:
                    print("FFmpeg error:", err)
                fut = asyncio.run_coroutine_threadsafe(self.play_next(), self.bot.loop)
                try:
                    fut.result()
                except Exception:
                    pass

            self.voice.play(source, after=after_play)


# ======================
# MUSIC COG
# ======================
class MusicYTCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.players: Dict[int, GuildPlayer] = {}

    def get_player(self, guild: discord.Guild) -> GuildPlayer:
        if guild.id not in self.players:
            self.players[guild.id] = GuildPlayer(self.bot, guild)
        return self.players[guild.id]

    # ======================
    # YT EXTRACTION
    # ======================
    async def extract_tracks(self, query: str):
        loop = asyncio.get_running_loop()
        func = functools.partial(YTDL.extract_info, query, download=False)

        try:
            info = await loop.run_in_executor(None, func)
        except Exception as e:
            return None, str(e)

        if not info:
            return None, "No results found."

        tracks: List[Track] = []

        # Playlist
        if "entries" in info and info["entries"]:
            for entry in info["entries"]:
                if not entry:
                    continue
                stream_url = entry.get("url")
                if not stream_url:
                    continue
                tracks.append(
                    Track(
                        title=entry.get("title", "Unknown"),
                        stream_url=stream_url,
                        duration=entry.get("duration", 0),
                        requester_id=0,
                    )
                )
            return tracks, None

        # Single video
        stream_url = info.get("url")
        if not stream_url:
            return None, "Could not extract stream."

        tracks.append(
            Track(
                title=info.get("title", "Unknown"),
                stream_url=stream_url,
                duration=info.get("duration", 0),
                requester_id=0,
            )
        )
        return tracks, None

    # ======================
    # PLAY
    # ======================
    @commands.hybrid_command(name="p", aliases=["play"], description="Play a song")
    async def play(self, ctx: commands.Context, *, query: str):
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.reply("❌ Join a voice channel first.", mention_author=False)

        player = self.get_player(ctx.guild)
        await player.connect(ctx.author.voice.channel)

        tracks, err = await self.extract_tracks(query)
        if err:
            return await ctx.reply(f"❌ {err}", mention_author=False)

        for t in tracks:
            t.requester_id = ctx.author.id
            player.queue.append(t)

        await ctx.reply(
            f"🎶 Added **{tracks[0].title}** to queue."
            if len(tracks) == 1
            else f"📂 Added playlist with **{len(tracks)}** tracks.",
            mention_author=False,
        )

        await player.play_next()

    # ======================
    # FREE COMMANDS
    # ======================
    @commands.hybrid_command(name="skip")
    async def skip(self, ctx: commands.Context):
        p = self.get_player(ctx.guild)
        if p.voice and p.voice.is_playing():
            p.voice.stop()
            await ctx.reply("⏭ Skipped.", mention_author=False)
        else:
            await ctx.reply("Nothing is playing.", mention_author=False)

    @commands.hybrid_command(name="queue")
    async def queue(self, ctx: commands.Context):
        p = self.get_player(ctx.guild)
        if not p.queue:
            return await ctx.reply("Queue is empty.", mention_author=False)
        lines = [f"`{i+1}.` {t.title}" for i, t in enumerate(p.queue[:15])]
        await ctx.reply("**Queue:**\n" + "\n".join(lines), mention_author=False)

    @commands.hybrid_command(name="nowplaying", aliases=["np"])
    async def nowplaying(self, ctx: commands.Context):
        p = self.get_player(ctx.guild)
        if not p.current:
            return await ctx.reply("Nothing is playing.", mention_author=False)
        await ctx.reply(f"🎵 **{p.current.title}**", mention_author=False)

    # ======================
    # PREMIUM COMMANDS
    # ======================
    async def is_premium(self, guild_id: int) -> bool:
        return await self.bot.db.is_premium_guild(guild_id)

    @commands.hybrid_command(name="loop")
    async def loop(self, ctx: commands.Context, mode: str):
        if not await self.is_premium(ctx.guild.id):
            return await ctx.reply("💎 Premium command.", mention_author=False)
        if mode not in ("off", "track", "queue"):
            return await ctx.reply("Use off / track / queue.", mention_author=False)
        self.get_player(ctx.guild).loop_mode = mode
        await ctx.reply(f"🔁 Loop set to **{mode}**", mention_author=False)

    @commands.hybrid_command(name="shuffle")
    async def shuffle(self, ctx: commands.Context):
        if not await self.is_premium(ctx.guild.id):
            return await ctx.reply("💎 Premium command.", mention_author=False)
        random.shuffle(self.get_player(ctx.guild).queue)
        await ctx.reply("🔀 Queue shuffled.", mention_author=False)

    @commands.hybrid_command(name="skipto")
    async def skipto(self, ctx: commands.Context, position: int):
        if not await self.is_premium(ctx.guild.id):
            return await ctx.reply("💎 Premium command.", mention_author=False)
        p = self.get_player(ctx.guild)
        if position < 1 or position > len(p.queue):
            return await ctx.reply("Invalid position.", mention_author=False)
        del p.queue[: position - 1]
        if p.voice:
            p.voice.stop()
        await ctx.reply(f"⏭ Skipped to position {position}.", mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(MusicYTCog(bot))
