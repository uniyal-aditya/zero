import asyncio
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import typing

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
        self.queue = asyncio.Queue()
        self.voice: discord.VoiceClient | None = None
        self.current: Track | None = None
        self.volume = 0.8
        self.lock = asyncio.Lock()

    async def connect(self, channel: discord.VoiceChannel):
        if self.voice is None or not self.voice.is_connected():
            self.voice = await channel.connect()

    async def play_next(self):
        async with self.lock:
            if self.voice is None or self.voice.is_playing():
                return
            if self.queue.empty():
                self.current = None
                return

            track: Track = await self.queue.get()

            source = discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(track.url, **FFMPEG_OPTIONS),
                volume=self.volume
            )

            self.current = track

            def after(_):
                asyncio.run_coroutine_threadsafe(
                    self.play_next(),
                    self.bot.loop
                )

            self.voice.play(source, after=after)

    async def add(self, track: Track):
        await self.queue.put(track)
        await self.play_next()

class MusicYT(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.players: dict[int, GuildPlayer] = {}

    def player(self, guild: discord.Guild):
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
            info = next(e for e in info["entries"] if e)

        return info["url"], info["title"]

    @commands.command(name="p", aliases=["play"])
    async def play_prefix(self, ctx: commands.Context, *, query: str):
        if not ctx.author.voice:
            return await ctx.send("Join a voice channel first.")

        player = self.player(ctx.guild)
        await player.connect(ctx.author.voice.channel)

        await ctx.typing()

        data = await self.yt_search(query)
        if not data:
            return await ctx.send("No results found.")

        url, title = data
        await player.add(Track(title, url, ctx.author))
        await ctx.send(f"🎵 Added **{title}**")

    @app_commands.command(name="play", description="Play a song")
    async def play_slash(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()

        if not interaction.user.voice:
            return await interaction.followup.send("Join a voice channel first.", ephemeral=True)

        player = self.player(interaction.guild)
        await player.connect(interaction.user.voice.channel)

        data = await self.yt_search(query)
        if not data:
            return await interaction.followup.send("No results found.", ephemeral=True)

        url, title = data
        await player.add(Track(title, url, interaction.user))
        await interaction.followup.send(f"🎵 Added **{title}**")

async def setup(bot):
    await bot.add_cog(MusicYT(bot))
