# core/player.py
import asyncio, logging, random
from dataclasses import dataclass, field
from typing import Optional
import discord
from discord.ext import commands

log = logging.getLogger("zero")

FFMPEG_BASE = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"

FILTERS = {
    "bassboost":  "-af bass=g=20,dynaudnorm=f=200",
    "nightcore":  "-af aresample=48000,asetrate=48000*1.25",
    "vaporwave":  "-af aresample=48000,asetrate=48000*0.8",
    "earrape":    "-af volume=20",
    "reset":      "",
}

@dataclass
class Track:
    title: str
    url: str          # direct stream URL
    webpage_url: str  # YouTube page URL for re-fetching
    duration: int     # seconds, 0 if unknown
    requester: discord.Member
    thumbnail: str = ""


class LoopMode:
    OFF   = "off"
    TRACK = "track"
    QUEUE = "queue"


class GuildPlayer:
    def __init__(self, bot: commands.Bot, guild: discord.Guild):
        self.bot    = bot
        self.guild  = guild
        self._queue: list[Track] = []
        self.voice: Optional[discord.VoiceClient] = None
        self.current: Optional[Track] = None
        self.volume  = 0.8
        self.loop    = LoopMode.OFF
        self.filter  = ""
        self._lock   = asyncio.Lock()

    # ── connection ────────────────────────────────────────────────────────────
    async def connect(self, channel: discord.VoiceChannel):
        if self.voice and self.voice.is_connected():
            if self.voice.channel.id != channel.id:
                await self.voice.move_to(channel)
        else:
            self.voice = await channel.connect(timeout=10.0)

    async def disconnect(self):
        self._queue.clear()
        self.current = None
        if self.voice:
            await self.voice.disconnect(force=True)
            self.voice = None

    # ── queue helpers ─────────────────────────────────────────────────────────
    def queue_list(self) -> list[Track]:
        return list(self._queue)

    def add_to_queue(self, track: Track):
        self._queue.append(track)

    def remove(self, index: int) -> Optional[Track]:
        if 0 <= index < len(self._queue):
            return self._queue.pop(index)
        return None

    def move(self, frm: int, to: int) -> bool:
        if not (0 <= frm < len(self._queue) and 0 <= to < len(self._queue)):
            return False
        t = self._queue.pop(frm)
        self._queue.insert(to, t)
        return True

    def shuffle(self):
        random.shuffle(self._queue)

    def clear_queue(self):
        self._queue.clear()

    # ── playback ──────────────────────────────────────────────────────────────
    def _make_source(self, url: str) -> discord.PCMVolumeTransformer:
        af = self.filter
        opts = f"-vn {af}" if af else "-vn"
        return discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(url,
                before_options=FFMPEG_BASE,
                options=opts),
            volume=self.volume
        )

    async def play_next(self):
        if self._lock.locked():
            return
        async with self._lock:
            if not self.voice or not self.voice.is_connected():
                return
            if self.voice.is_playing() or self.voice.is_paused():
                return

            # Loop track
            if self.loop == LoopMode.TRACK and self.current:
                track = self.current
            # Loop queue
            elif self.loop == LoopMode.QUEUE and self.current:
                self._queue.append(self.current)
                if not self._queue:
                    self.current = None
                    return
                track = self._queue.pop(0)
            # Normal
            else:
                if not self._queue:
                    self.current = None
                    return
                track = self._queue.pop(0)

            # Refresh stream URL
            from core.ytdl import fetch_track
            try:
                refreshed = await fetch_track(track.webpage_url)
                if refreshed:
                    track = Track(
                        title=track.title,
                        url=refreshed["url"],
                        webpage_url=track.webpage_url,
                        duration=track.duration,
                        requester=track.requester,
                        thumbnail=track.thumbnail,
                    )
            except Exception as e:
                log.warning("URL refresh failed for %s: %s", track.title, e)

            self.current = track

            try:
                source = self._make_source(track.url)
            except Exception as e:
                log.error("FFmpeg source error: %s", e)
                asyncio.run_coroutine_threadsafe(self.play_next(), self.bot.loop)
                return

            def after(err):
                if err:
                    log.error("Playback error: %s", err)
                asyncio.run_coroutine_threadsafe(self.play_next(), self.bot.loop)

            self.voice.play(source, after=after)
            log.info("[%s] Now playing: %s", self.guild.name, track.title)

    async def start(self):
        """Start playback if not already playing."""
        if self.voice and not self.voice.is_playing() and not self.voice.is_paused():
            await self.play_next()

    def pause(self):
        if self.voice and self.voice.is_playing():
            self.voice.pause()

    def resume(self):
        if self.voice and self.voice.is_paused():
            self.voice.resume()

    def skip(self):
        if self.voice and (self.voice.is_playing() or self.voice.is_paused()):
            self.voice.stop()  # triggers after → play_next

    def skipto(self, index: int) -> bool:
        """1-based. Removes tracks before index and skips current."""
        if index < 1 or index > len(self._queue):
            return False
        self._queue = self._queue[index - 1:]
        self.skip()
        return True

    def set_volume(self, vol: float):
        self.volume = max(0.0, min(vol, 2.0))
        if self.voice and self.voice.source and isinstance(self.voice.source, discord.PCMVolumeTransformer):
            self.voice.source.volume = self.volume

    def set_filter(self, name: str) -> bool:
        if name not in FILTERS:
            return False
        self.filter = FILTERS[name]
        # Restart current track with new filter
        if self.voice and self.voice.is_playing() and self.current:
            self.voice.stop()  # after callback re-queues and plays with new filter
            self._queue.insert(0, self.current)
            self.current = None
        return True

    def format_duration(self, seconds: int) -> str:
        if seconds <= 0:
            return "Live"
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
