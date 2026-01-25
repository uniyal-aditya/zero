# cogs/music_yt.py
import asyncio
import functools
import random
from dataclasses import dataclass
from typing import Optional, List, Dict

import discord
from discord.ext import commands
import yt_dlp

FFMPEG_OPTIONS = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
YTDL_OPTS = {
    "format": "bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch",
    "skip_download": True,
}
YTDL = yt_dlp.YoutubeDL(YTDL_OPTS)

@dataclass
class Track:
    title: str
    url: str
    duration: int
    requester_id: int

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
        if not self.voice:
            self.voice = await channel.connect()

    async def play_next(self):
        async with self.lock:
            # decide next track
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
                    track.url,
                    before_options=FFMPEG_OPTIONS,
                    options="-vn"
                ),
                volume=self.volume
            )

            def _after(err):
                fut = asyncio.run_coroutine_threadsafe(self.play_next(), self.bot.loop)
                try:
                    fut.result()
                except Exception:
                    pass

            # play
            if self.voice:
                self.voice.play(source, after=_after)

class MusicYTCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.players: Dict[int, GuildPlayer] = {}
        self._ytdl_executor = asyncio.get_running_loop()

    def get_player(self, guild: discord.Guild) -> GuildPlayer:
        p = self.players.get(guild.id)
        if not p:
            p = GuildPlayer(self.bot, guild)
            self.players[guild.id] = p
        return p

    async def extract_tracks(self, query: str):
        loop = asyncio.get_running_loop()
        func = functools.partial(YTDL.extract_info, query, download=False)
        try:
            info = await loop.run_in_executor(None, func)
        except Exception as e:
            return None, str(e)
        if not info:
            return None, "No results"
        tracks = []
        # playlist
        if "entries" in info and info["entries"]:
            for e in info["entries"]:
                if not e:
                    continue
                url = e.get("url") or e.get("webpage_url")
                tracks.append(Track(title=e.get("title", "Unknown"), url=url, duration=e.get("duration", 0), requester_id=0))
            return tracks, None
        # single
        url = info.get("url") or info.get("webpage_url")
        tracks.append(Track(title=info.get("title", "Unknown"), url=url, duration=info.get("duration", 0), requester_id=0))
        return tracks, None

    # ------------------ PLAY ------------------
    @commands.hybrid_command(name="p", aliases=["play"], description="Play a song (YouTube link or search)")
    async def play(self, ctx: commands.Context, *, query: str):
        # Ensure voice
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.reply("❌ Join a voice channel first.", mention_author=False)

        player = self.get_player(ctx.guild)
        await player.connect(ctx.author.voice.channel)

        # extract info in executor
        tracks, err = await self.extract_tracks(query)
        if err:
            return await ctx.reply(f"❌ Error: {err}", mention_author=False)
        if not tracks:
            return await ctx.reply("❌ No results found.", mention_author=False)

        # attach requester id properly
        for t in tracks:
            t.requester_id = ctx.author.id
            player.queue.append(t)

        if len(tracks) > 1:
            await ctx.reply(f"📂 Added playlist with **{len(tracks)}** tracks.", mention_author=False)
        else:
            await ctx.reply(f"🎶 Added **{tracks[0].title}** to queue.", mention_author=False)

        # start playback if not playing
        if not player.voice.is_playing():
            await player.play_next()

    # ------------------ BASIC CONTROLS (Free) ------------------
    @commands.hybrid_command(name="skip", description="Skip current track")
    async def skip(self, ctx: commands.Context):
        p = self.get_player(ctx.guild)
        if p.voice and p.voice.is_playing():
            p.voice.stop()
            await ctx.reply("⏭ Skipped.", mention_author=False)
        else:
            await ctx.reply("Nothing is playing.", mention_author=False)

    @commands.hybrid_command(name="queue", description="Show queue")
    async def queue(self, ctx: commands.Context):
        p = self.get_player(ctx.guild)
        if not p.queue:
            return await ctx.reply("Queue is empty.", mention_author=False)
        lines = []
        for i, t in enumerate(p.queue[:15], start=1):
            lines.append(f"`{i}.` {t.title} [{t.duration}s]")
        await ctx.reply("**Queue (next 15):**\n" + "\n".join(lines), mention_author=False)

    @commands.hybrid_command(name="nowplaying", aliases=["np"], description="Show currently playing")
    async def nowplaying(self, ctx: commands.Context):
        p = self.get_player(ctx.guild)
        if not p.current:
            return await ctx.reply("Nothing is playing.", mention_author=False)
        # requester name if available
        requester = ctx.guild.get_member(p.current.requester_id)
        requester_name = requester.display_name if requester else "Unknown"
        await ctx.reply(f"🎵 **{p.current.title}** — requested by {requester_name}", mention_author=False)

    @commands.hybrid_command(name="pause", description="Pause playback")
    async def pause(self, ctx: commands.Context):
        vc = ctx.guild.voice_client
        if vc and vc.is_playing():
            vc.pause()
            await ctx.reply("⏸ Paused.", mention_author=False)
        else:
            await ctx.reply("Nothing is playing.", mention_author=False)

    @commands.hybrid_command(name="resume", description="Resume playback")
    async def resume(self, ctx: commands.Context):
        vc = ctx.guild.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await ctx.reply("▶ Resumed.", mention_author=False)
        else:
            await ctx.reply("Nothing is paused.", mention_author=False)

    @commands.hybrid_command(name="stop", description="Stop and clear queue")
    async def stop(self, ctx: commands.Context):
        p = self.get_player(ctx.guild)
        if p.voice:
            try:
                await p.voice.disconnect()
            except Exception:
                pass
        p.voice = None
        p.current = None
        p.queue.clear()
        await ctx.reply("⏹ Stopped and cleared queue.", mention_author=False)

    @commands.hybrid_command(name="volume", description="Set volume 0-200")
    async def volume(self, ctx: commands.Context, value: int):
        if value < 0 or value > 200:
            return await ctx.reply("Volume must be between 0 and 200.", mention_author=False)
        p = self.get_player(ctx.guild)
        p.volume = value / 100.0
        await ctx.reply(f"🔊 Volume set to {value}%", mention_author=False)

    # ------------------ PREMIUM CONTROLS ------------------
    async def _premium_check(self, guild_id: int) -> bool:
        try:
            return await self.bot.db.is_premium_guild(guild_id)
        except Exception:
            # On DB failure, treat as not premium
            return False

    @commands.hybrid_command(name="loop", description="Set loop: off/track/queue (Premium)")
    async def loop(self, ctx: commands.Context, mode: str):
        if not await self._premium_check(ctx.guild.id):
            return await ctx.reply("💎 This is a premium command. Ask the server owner to enable premium.", mention_author=False)
        mode = mode.lower()
        if mode not in ("off", "track", "queue"):
            return await ctx.reply("Invalid mode. Use `off`, `track` or `queue`.", mention_author=False)
        p = self.get_player(ctx.guild)
        p.loop_mode = mode
        await ctx.reply(f"🔁 Loop mode set to **{mode}**", mention_author=False)

    @commands.hybrid_command(name="shuffle", description="Shuffle queue (Premium)")
    async def shuffle(self, ctx: commands.Context):
        if not await self._premium_check(ctx.guild.id):
            return await ctx.reply("💎 This is a premium command. Ask the server owner to enable premium.", mention_author=False)
        p = self.get_player(ctx.guild)
        random.shuffle(p.queue)
        await ctx.reply("🔀 Queue shuffled.", mention_author=False)

    @commands.hybrid_command(name="skipto", description="Skip to queue position (Premium)")
    async def skipto(self, ctx: commands.Context, position: int):
        if not await self._premium_check(ctx.guild.id):
            return await ctx.reply("💎 This is a premium command. Ask the server owner to enable premium.", mention_author=False)
        p = self.get_player(ctx.guild)
        if position < 1 or position > len(p.queue):
            return await ctx.reply("Position out of range.", mention_author=False)
        # drop entries before desired
        del p.queue[: position - 1]
        if p.voice and p.voice.is_playing():
            p.voice.stop()
        await ctx.reply(f"⏭ Skipped to position {position}.", mention_author=False)

async def setup(bot: commands.Bot):
    await bot.add_cog(MusicYTCog(bot))
