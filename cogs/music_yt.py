# cogs/music_yt.py
import asyncio
import shlex
import functools
import typing
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

import discord
from discord.ext import commands
from discord import app_commands

import yt_dlp

FFMPEG_OPTIONS = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"

# You may tune this executor size
_YTDL_EXECUTOR = ThreadPoolExecutor(max_workers=4)

ydl_opts = {
    "format": "bestaudio/best",
    "noplaylist": False,    # allow playlists; will handle
    "quiet": True,
    "no_warnings": True,
    "ignoreerrors": True,
    "default_search": "ytsearch",  # if raw text is given, search YouTube
    # avoid downloading; we only want info/URL
    "skip_download": True,
}


@dataclass
class Track:
    title: str
    url: str  # direct audio stream url or webpage url (ffmpeg will read it)
    webpage_url: str
    duration: int  # seconds (may be 0 if unknown)
    requester: typing.Union[discord.Member, discord.User]


class YTDLSource:
    @staticmethod
    def extract_info(query: str, *, loop: asyncio.AbstractEventLoop = None):
        """
        Blocking call to yt-dlp to extract information for query.
        Returns info dict or None.
        """
        # We call yt_dlp.YoutubeDL.extract_info in a thread to avoid blocking the event loop.
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # If query is a URL to a playlist, ydl.extract_info returns playlist dict
            return ydl.extract_info(query, download=False)

    @classmethod
    async def get_tracks(cls, query: str, requester, *, loop=None):
        """
        Resolve query to one or more Track objects.
        query can be:
         - a full youtube URL
         - a playlist URL
         - raw search terms (ytsearch)
        """
        if loop is None:
            loop = asyncio.get_event_loop()

        func = functools.partial(cls.extract_info, query)
        try:
            info = await loop.run_in_executor(_YTDL_EXECUTOR, func)
        except Exception as e:
            return None, f"yt-dlp error: {e}"

        if not info:
            return None, "No results."

        tracks = []

        # If it's a playlist
        if "entries" in info and info.get("entries"):
            for entry in info["entries"]:
                if not entry:
                    continue
                # some entries may be None with ignoreerrors True
                audio_url = entry.get("url")
                # yt-dlp may provide direct url fragments; prefer 'url' + 'protocol' handled by ffmpeg
                t = Track(
                    title=entry.get("title") or "Unknown title",
                    url=entry.get("url") or entry.get("webpage_url"),
                    webpage_url=entry.get("webpage_url"),
                    duration=entry.get("duration") or 0,
                    requester=requester,
                )
                tracks.append(t)
            return tracks, None

        # Single video
        # Sometimes info has 'url' pointing to format id; ffmpeg can accept the 'webpage_url' too.
        if info.get("url") and info.get("webpage_url"):
            t = Track(
                title=info.get("title", "Unknown"),
                url=info.get("url") or info.get("webpage_url"),
                webpage_url=info.get("webpage_url"),
                duration=info.get("duration") or 0,
                requester=requester,
            )
            tracks.append(t)
            return tracks, None

        # Fallback: create a track with webpage_url
        t = Track(
            title=info.get("title", "Unknown"),
            url=info.get("webpage_url"),
            webpage_url=info.get("webpage_url"),
            duration=info.get("duration") or 0,
            requester=requester,
        )
        tracks.append(t)
        return tracks, None


class GuildPlayer:
    """
    Holds the voice client, queue and playback state for a guild.
    """
    def __init__(self, bot: commands.Bot, guild: discord.Guild):
        self.bot = bot
        self.guild = guild
        self.queue: asyncio.Queue = asyncio.Queue()
        self.current: typing.Optional[Track] = None
        self.voice: typing.Optional[discord.VoiceClient] = None
        self._play_lock = asyncio.Lock()
        self._volume = 0.8  # 0.0 - 1.0

    async def ensure_voice(self, ctx):
        # Connect if not connected
        if ctx.author.voice and ctx.author.voice.channel:
            channel = ctx.author.voice.channel
            if self.guild.voice_client is None:
                self.voice = await channel.connect()
            else:
                self.voice = self.guild.voice_client
            return True
        return False

    async def enqueue(self, track: Track):
        await self.queue.put(track)

    async def play_next(self):
        """
        Pull next from queue and play. This is called in after callback.
        """
        async with self._play_lock:
            if self.voice is None:
                return
            if self.voice.is_playing() or self.voice.is_paused():
                return
            try:
                nxt: Track = await asyncio.wait_for(self.queue.get(), timeout=0.1)
            except asyncio.TimeoutError:
                self.current = None
                return
            # create FFmpegPCMAudio
            source = discord.FFmpegPCMAudio(
                nxt.url,
                before_options=FFMPEG_OPTIONS,
                options="-vn"
            )
            # apply volume transformer
            player = discord.PCMVolumeTransformer(source, volume=self._volume)
            def _after(err):
                fut = asyncio.run_coroutine_threadsafe(self.play_next(), self.bot.loop)
                try:
                    fut.result()
                except Exception:
                    pass
            self.current = nxt
            self.voice.play(player, after=_after)

    async def start_playback_if_needed(self):
        async with self._play_lock:
            if self.voice is None or self.voice.is_playing() or self.voice.is_paused():
                return
            if self.queue.empty():
                return
            nxt: Track = await self.queue.get()
            source = discord.FFmpegPCMAudio(
                nxt.url,
                before_options=FFMPEG_OPTIONS,
                options="-vn"
            )
            player = discord.PCMVolumeTransformer(source, volume=self._volume)
            def _after(err):
                fut = asyncio.run_coroutine_threadsafe(self.play_next(), self.bot.loop)
                try:
                    fut.result()
                except Exception:
                    pass
            self.current = nxt
            self.voice.play(player, after=_after)

    # helper controls
    async def skip(self):
        if self.voice and self.voice.is_playing():
            self.voice.stop()

    async def stop_and_clear(self):
        if self.voice:
            try:
                await self.voice.disconnect()
            except Exception:
                pass
        # clear queue
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except Exception:
                break
        self.current = None

    def set_volume(self, vol: float):
        self._volume = max(0.0, min(2.0, vol))  # allow up to 2.0
        # changing volume on current player is not straightforward; will affect next songs

class MusicYTCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.players: typing.Dict[int, GuildPlayer] = {}  # guild_id -> player

    def get_player(self, guild: discord.Guild) -> GuildPlayer:
        p = self.players.get(guild.id)
        if not p:
            p = GuildPlayer(self.bot, guild)
            self.players[guild.id] = p
        return p

    # JOIN
    @commands.command(name="join")
    async def join_prefix(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send("Join a voice channel first.")
        player = self.get_player(ctx.guild)
        await player.ensure_voice(ctx)
        await ctx.send("✅ Joined.")

    # PLAY (prefix .p and slash)
    @commands.command(name="p", aliases=["play"])
    async def play_prefix(self, ctx: commands.Context, *, query: str):
        # ensure voice
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send("Join a voice channel first.")
        player = self.get_player(ctx.guild)
        await player.ensure_voice(ctx)
        await ctx.trigger_typing()
        tracks, err = await YTDLSource.get_tracks(query, requester=ctx.author)
        if err:
            return await ctx.send(f"Error: {err}")
        if not tracks:
            return await ctx.send("No results.")
        # If multiple (playlist), add all; else add first
        if len(tracks) > 1:
            for t in tracks:
                await player.enqueue(t)
            await ctx.send(f"📂 Added playlist with {len(tracks)} tracks.")
        else:
            t = tracks[0]
            await player.enqueue(t)
            await ctx.send(f"🎶 Added **{t.title}** to queue.")
        await player.start_playback_if_needed()

    @app_commands.command(name="play", description="Play a song (YouTube or search)")
    @app_commands.describe(query="YouTube link or search query")
    async def play_slash(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        ctx = await self.bot.get_context(interaction.message) if interaction.message else None
        player = self.get_player(interaction.guild)
        # ensure voice - require owner to be in vc
        user = interaction.user
        if not getattr(user, "voice", None) or not user.voice:
            return await interaction.followup.send("Join a voice channel first.", ephemeral=True)
        await player.ensure_voice(interaction)
        tracks, err = await YTDLSource.get_tracks(query, requester=interaction.user)
        if err:
            return await interaction.followup.send(f"Error: {err}", ephemeral=True)
        if not tracks:
            return await interaction.followup.send("No results.", ephemeral=True)
        if len(tracks) > 1:
            for t in tracks:
                await player.enqueue(t)
            await interaction.followup.send(f"📂 Added playlist with {len(tracks)} tracks.", ephemeral=True)
        else:
            t = tracks[0]
            await player.enqueue(t)
            await interaction.followup.send(f"🎶 Added **{t.title}** to queue.", ephemeral=True)
        await player.start_playback_if_needed()

    # SKIP
    @commands.command(name="skip")
    async def skip_prefix(self, ctx: commands.Context):
        player = self.get_player(ctx.guild)
        await player.skip()
        await ctx.send("⏭ Skipped.")

    # STOP / LEAVE
    @commands.command(name="stop")
    async def stop_prefix(self, ctx: commands.Context):
        player = self.get_player(ctx.guild)
        await player.stop_and_clear()
        await ctx.send("Stopped and left.")

    @commands.command(name="pause")
    async def pause_prefix(self, ctx: commands.Context):
        p = self.get_player(ctx.guild)
        if not p.voice or not p.voice.is_playing():
            return await ctx.send("Nothing is playing.")
        p.voice.pause()
        await ctx.send("⏸ Paused.")

    @commands.command(name="resume")
    async def resume_prefix(self, ctx: commands.Context):
        p = self.get_player(ctx.guild)
        if not p.voice or not p.voice.is_paused():
            return await ctx.send("Nothing paused.")
        p.voice.resume()
        await ctx.send("▶ Resumed.")

    @commands.command(name="nowplaying", aliases=["np"])
    async def nowplaying(self, ctx: commands.Context):
        p = self.get_player(ctx.guild)
        if not p.current:
            return await ctx.send("Nothing is playing.")
        t = p.current
        await ctx.send(f"Now playing: **{t.title}** — requested by {t.requester.display_name}")

    @commands.command(name="queue")
    async def show_queue(self, ctx: commands.Context):
        p = self.get_player(ctx.guild)
        if p.queue.empty():
            return await ctx.send("Queue is empty.")
        # we can't inspect asyncio.Queue easily; but we used a simple queue - let's pull items quickly
        # For display we'll use a snapshot: convert to list by draining and re-adding (careful to preserve order)
        items = []
        while not p.queue.empty():
            try:
                items.append(p.queue.get_nowait())
            except Exception:
                break
        # re-add in same order
        for it in items:
            await p.queue.put(it)
        lines = []
        for i, it in enumerate(items[:15], start=1):
            lines.append(f"`{i}.` {it.title} [{it.duration}s] — requested by {it.requester.display_name}")
        await ctx.send("**Queue:**\n" + "\n".join(lines))

    @commands.command(name="volume")
    async def set_volume(self, ctx: commands.Context, vol: float):
        p = self.get_player(ctx.guild)
        if vol < 0 or vol > 2.0:
            return await ctx.send("Volume must be between 0.0 and 2.0")
        p.set_volume(vol)
        await ctx.send(f"Volume set to {vol}")

async def setup(bot):
    await bot.add_cog(MusicYTCog(bot))
