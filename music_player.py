from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Optional

import discord
from discord.ext import commands
from yt_dlp import YoutubeDL

YDL_OPTS = {
    "format": "bestaudio/best",
    "noplaylist": False,
    "quiet": True,
    "default_search": "ytsearch",
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}


@dataclass
class Track:
    url: str
    title: str
    webpage_url: str
    duration: Optional[int] = None


class MusicQueue:
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.queue: list[Track] = []
        self.current: Optional[Track] = None
        self.loop_single: bool = False
        self.loop_queue: bool = False
        self.autoplay: bool = False
        self._play_next = asyncio.Event()

    def add(self, tracks: list[Track]) -> None:
        self.queue.extend(tracks)

    def shuffle(self) -> None:
        import random

        random.shuffle(self.queue)

    def clear(self) -> None:
        self.queue.clear()


class MusicCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.queues: dict[int, MusicQueue] = {}
        self.ydl = YoutubeDL(YDL_OPTS)

    def get_queue(self, guild_id: int) -> MusicQueue:
        if guild_id not in self.queues:
            self.queues[guild_id] = MusicQueue(self.bot)
        return self.queues[guild_id]

    async def ensure_voice(
        self, ctx: commands.Context, *, respond_ephemeral: bool = False
    ) -> Optional[discord.VoiceClient]:
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.reply(
                "You need to be in a voice channel to use music commands.",
                mention_author=False,
            )
            return None

        voice = ctx.voice_client
        if voice is None:
            voice = await ctx.author.voice.channel.connect(self_deaf=True)
        elif voice.channel != ctx.author.voice.channel:
            await voice.move_to(ctx.author.voice.channel)
        return voice

    def _extract_tracks(self, query: str) -> list[Track]:
        data = self.ydl.extract_info(query, download=False)
        entries = []
        if "entries" in data:
            entries = data["entries"]
        else:
            entries = [data]

        tracks: list[Track] = []
        for e in entries:
            if not e:
                continue
            tracks.append(
                Track(
                    url=e.get("url") or e.get("webpage_url"),
                    title=e.get("title", "Unknown title"),
                    webpage_url=e.get("webpage_url") or query,
                    duration=e.get("duration"),
                )
            )
        return tracks

    async def _play_loop(self, ctx: commands.Context, queue: MusicQueue) -> None:
        voice = ctx.voice_client
        if not voice:
            return

        while True:
            if queue.loop_single and queue.current:
                track = queue.current
            else:
                if not queue.queue:
                    queue.current = None
                    break
                track = queue.queue.pop(0)
                queue.current = track

            source = await self.bot.loop.run_in_executor(
                None,
                lambda: discord.FFmpegPCMAudio(
                    track.url,
                    **FFMPEG_OPTIONS,
                ),
            )

            voice.play(
                source,
                after=lambda _: self.bot.loop.call_soon_threadsafe(
                    queue._play_next.set
                ),
            )

            await ctx.send(
                f"🎵 Now playing: **{track.title}**",
                allowed_mentions=discord.AllowedMentions.none(),
            )

            await queue._play_next.wait()
            queue._play_next.clear()

            if queue.loop_queue and not queue.loop_single and track:
                queue.queue.append(track)

            if not voice.is_connected():
                break

    @commands.hybrid_command(name="play", aliases=["p"], description="Play music from YouTube / Spotify links or search.")
    async def play(self, ctx: commands.Context, *, query: str) -> None:
        voice = await self.ensure_voice(ctx)
        if not voice:
            return

        await ctx.typing()
        try:
            tracks = await self.bot.loop.run_in_executor(
                None, lambda: self._extract_tracks(query)
            )
        except Exception:
            await ctx.reply("Could not find any results for that query.", mention_author=False)
            return

        if not tracks:
            await ctx.reply("No results found.", mention_author=False)
            return

        queue = self.get_queue(ctx.guild.id)
        queue.add(tracks)

        if not voice.is_playing() and not voice.is_paused():
            await self._play_loop(ctx, queue)
        else:
            await ctx.reply(
                f"Queued **{len(tracks)}** track(s).",
                mention_author=False,
            )

    @commands.hybrid_command(name="skip", description="Skip the current track.")
    async def skip(self, ctx: commands.Context) -> None:
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            await ctx.reply("Nothing is playing.", mention_author=False)
            return
        ctx.voice_client.stop()
        await ctx.reply("⏭ Skipped.", mention_author=False)

    @commands.hybrid_command(name="pause", description="Pause the current track.")
    async def pause(self, ctx: commands.Context) -> None:
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            await ctx.reply("Nothing is playing.", mention_author=False)
            return
        ctx.voice_client.pause()
        await ctx.reply("⏸ Paused.", mention_author=False)

    @commands.hybrid_command(name="resume", description="Resume the current track.")
    async def resume(self, ctx: commands.Context) -> None:
        if not ctx.voice_client or not ctx.voice_client.is_paused():
            await ctx.reply("Nothing is paused.", mention_author=False)
            return
        ctx.voice_client.resume()
        await ctx.reply("▶️ Resumed.", mention_author=False)

    @commands.hybrid_command(name="stop", description="Stop playback and clear the queue.")
    async def stop(self, ctx: commands.Context) -> None:
        if ctx.voice_client:
            ctx.voice_client.stop()
            await ctx.voice_client.disconnect(force=True)
        queue = self.get_queue(ctx.guild.id)
        queue.clear()
        queue.current = None
        await ctx.reply("⏹ Stopped and cleared the queue.", mention_author=False)

    @commands.hybrid_command(name="shuffle", description="Shuffle the queue.")
    async def shuffle(self, ctx: commands.Context) -> None:
        queue = self.get_queue(ctx.guild.id)
        if not queue.queue:
            await ctx.reply("Queue is empty.", mention_author=False)
            return
        queue.shuffle()
        await ctx.reply("🔀 Shuffled the queue.", mention_author=False)

    @commands.hybrid_command(name="loop", description="Set loop mode: off / track / queue / autoplay.")
    async def loop(self, ctx: commands.Context, mode: str) -> None:
        mode = mode.lower()
        queue = self.get_queue(ctx.guild.id)

        if mode == "off":
            queue.loop_single = False
            queue.loop_queue = False
            queue.autoplay = False
        elif mode == "track":
            queue.loop_single = True
            queue.loop_queue = False
            queue.autoplay = False
        elif mode == "queue":
            queue.loop_single = False
            queue.loop_queue = True
            queue.autoplay = False
        elif mode == "autoplay":
            queue.autoplay = True
        else:
            await ctx.reply(
                "Invalid mode. Use `off`, `track`, `queue`, or `autoplay`.",
                mention_author=False,
            )
            return

        await ctx.reply(f"Loop mode set to **{mode}**.", mention_author=False)

    @commands.hybrid_command(name="nowplaying", description="Show the currently playing track.")
    async def nowplaying(self, ctx: commands.Context) -> None:
        queue = self.get_queue(ctx.guild.id)
        if not queue.current:
            await ctx.reply("Nothing is playing right now.", mention_author=False)
            return
        await ctx.reply(
            f"🎵 Now playing: **{queue.current.title}**",
            mention_author=False,
        )

    @commands.hybrid_command(name="queue", description="Show the current queue.")
    async def queue_cmd(self, ctx: commands.Context) -> None:
        queue = self.get_queue(ctx.guild.id)
        if not queue.queue and not queue.current:
            await ctx.reply("Queue is empty.", mention_author=False)
            return

        lines = []
        if queue.current:
            lines.append(f"**Now:** {queue.current.title}")
        for idx, track in enumerate(queue.queue[:10], start=1):
            lines.append(f"{idx}. {track.title}")
        if len(queue.queue) > 10:
            lines.append(f"... and {len(queue.queue) - 10} more.")

        await ctx.reply("\n".join(lines), mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MusicCog(bot))

