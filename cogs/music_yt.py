# cogs/music_yt.py
import asyncio
import random
from dataclasses import dataclass
from typing import Optional, Dict, List

import discord
from discord.ext import commands
import yt_dlp

FFMPEG_OPTIONS = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"

YTDL_OPTS = {
    "format": "bestaudio/best",
    "quiet": True,
    "default_search": "ytsearch",
    "skip_download": True,
}

@dataclass
class Track:
    title: str
    url: str
    duration: int
    requester: discord.Member

class GuildPlayer:
    def __init__(self, bot: commands.Bot, guild: discord.Guild):
        self.bot = bot
        self.guild = guild
        self.queue: List[Track] = []
        self.current: Optional[Track] = None
        self.voice: Optional[discord.VoiceClient] = None
        self.loop_mode: str = "off"  # off | track | queue

    async def connect(self, channel: discord.VoiceChannel):
        if not self.voice:
            self.voice = await channel.connect()

    async def play_next(self):
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

        source = discord.FFmpegPCMAudio(
            track.url,
            before_options=FFMPEG_OPTIONS,
            options="-vn",
        )

        def after(_):
            fut = asyncio.run_coroutine_threadsafe(
                self.play_next(), self.bot.loop
            )
            try:
                fut.result()
            except:
                pass

        self.voice.play(source, after=after)

class MusicYTCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.players: Dict[int, GuildPlayer] = {}

    def player(self, guild: discord.Guild):
        if guild.id not in self.players:
            self.players[guild.id] = GuildPlayer(self.bot, guild)
        return self.players[guild.id]

    async def is_premium(self, guild_id: int) -> bool:
        return await self.bot.db.is_premium_guild(guild_id)

    async def extract(self, query: str, requester):
        with yt_dlp.YoutubeDL(YTDL_OPTS) as ydl:
            info = ydl.extract_info(query, download=False)

        tracks = []
        if "entries" in info:
            for e in info["entries"]:
                if e:
                    tracks.append(
                        Track(e["title"], e["url"], e.get("duration", 0), requester)
                    )
        else:
            tracks.append(
                Track(info["title"], info["url"], info.get("duration", 0), requester)
            )
        return tracks

    # ================= PLAY =================
    @commands.hybrid_command(name="p", aliases=["play"], description="Play a song")
    async def play(self, ctx: commands.Context, *, query: str):
        if not ctx.author.voice:
            return await ctx.reply("❌ Join a voice channel first.")

        player = self.player(ctx.guild)
        await player.connect(ctx.author.voice.channel)

        tracks = await self.extract(query, ctx.author)
        for t in tracks:
            player.queue.append(t)

        await ctx.reply(f"🎶 Added **{len(tracks)}** track(s).")
        if not player.voice.is_playing():
            await player.play_next()

    # ================= FREE =================
    @commands.hybrid_command(name="skip")
    async def skip(self, ctx):
        p = self.player(ctx.guild)
        if p.voice:
            p.voice.stop()
        await ctx.reply("⏭ Skipped.")

    @commands.hybrid_command(name="queue")
    async def queue(self, ctx):
        p = self.player(ctx.guild)
        if not p.queue:
            return await ctx.reply("Queue is empty.")
        text = "\n".join(f"{i+1}. {t.title}" for i, t in enumerate(p.queue[:10]))
        await ctx.reply(f"**Queue:**\n{text}")

    # ================= PREMIUM =================
    @commands.hybrid_command(name="loop")
    async def loop(self, ctx, mode: str):
        if not await self.is_premium(ctx.guild.id):
            return await ctx.reply("💎 Premium command. Upgrade this server.")

        if mode not in ("off", "track", "queue"):
            return await ctx.reply("Modes: off / track / queue")

        self.player(ctx.guild).loop_mode = mode
        await ctx.reply(f"🔁 Loop mode set to **{mode}**")

    @commands.hybrid_command(name="shuffle")
    async def shuffle(self, ctx):
        if not await self.is_premium(ctx.guild.id):
            return await ctx.reply("💎 Premium command. Upgrade this server.")

        p = self.player(ctx.guild)
        random.shuffle(p.queue)
        await ctx.reply("🔀 Queue shuffled.")

    @commands.hybrid_command(name="skipto")
    async def skipto(self, ctx, position: int):
        if not await self.is_premium(ctx.guild.id):
            return await ctx.reply("💎 Premium command. Upgrade this server.")

        p = self.player(ctx.guild)
        if position < 1 or position > len(p.queue):
            return await ctx.reply("Invalid position.")
        del p.queue[: position - 1]
        if p.voice:
            p.voice.stop()
        await ctx.reply(f"⏭ Skipped to position {position}.")

async def setup(bot):
    await bot.add_cog(MusicYTCog(bot))
