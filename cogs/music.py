# cogs/music.py
import discord
from discord.ext import commands
import wavelink
import asyncio

from core.player import MusicPlayer
import config


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ======================
    # VOICE CHECK
    # ======================
    async def ensure_voice(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.reply("❌ Join a voice channel first.", mention_author=False)
            return None

        vc = ctx.guild.voice_client
        if not vc:
            await ctx.author.voice.channel.connect(cls=MusicPlayer)
            vc = ctx.guild.voice_client

        return vc

    # ======================
    # JOIN
    # ======================
    @commands.hybrid_command(name="join", description="Join your voice channel")
    async def join(self, ctx: commands.Context):
        vc = await self.ensure_voice(ctx)
        if vc:
            await ctx.reply("✅ Joined your voice channel.", mention_author=False)

    # ======================
    # PLAY (PRIMARY = .p)
    # ======================
    @commands.hybrid_command(
        name="p",
        aliases=["play"],
        description="Play a song from YouTube"
    )
    async def p(self, ctx: commands.Context, *, query: str):
        vc = await self.ensure_voice(ctx)
        if not vc:
            return

        try:
            tracks = await wavelink.YouTubeTrack.search(query)
        except Exception:
            return await ctx.reply("❌ Failed to search.", mention_author=False)

        if not tracks:
            return await ctx.reply("❌ No results found.", mention_author=False)

        track = tracks[0]
        await vc.queue.put(track)

        await ctx.reply(
            f"🎶 Added **{track.title}** to the queue",
            mention_author=False
        )

        if not vc.playing:
            await vc.play(await vc.queue.get())

    # ======================
    # SKIP
    # ======================
    @commands.hybrid_command(name="skip", description="Skip the current track")
    async def skip(self, ctx: commands.Context):
        vc = ctx.guild.voice_client
        if not vc or not vc.playing:
            return await ctx.reply("❌ Nothing is playing.", mention_author=False)

        await vc.stop()
        await ctx.reply("⏭️ Skipped.", mention_author=False)

    # ======================
    # STOP / LEAVE
    # ======================
    @commands.hybrid_command(name="stop", description="Stop music and leave")
    async def stop(self, ctx: commands.Context):
        vc = ctx.guild.voice_client
        if not vc:
            return await ctx.reply("❌ Not connected.", mention_author=False)

        vc.queue.clear()
        await vc.stop()
        await vc.disconnect()
        await ctx.reply("⏹️ Stopped and left the channel.", mention_author=False)

    # ======================
    # PAUSE / RESUME
    # ======================
    @commands.hybrid_command(name="pause", description="Pause playback")
    async def pause(self, ctx: commands.Context):
        vc = ctx.guild.voice_client
        if not vc or not vc.playing:
            return await ctx.reply("❌ Nothing is playing.", mention_author=False)

        await vc.pause()
        await ctx.reply("⏸️ Paused.", mention_author=False)

    @commands.hybrid_command(name="resume", description="Resume playback")
    async def resume(self, ctx: commands.Context):
        vc = ctx.guild.voice_client
        if not vc:
            return await ctx.reply("❌ Not connected.", mention_author=False)

        await vc.resume()
        await ctx.reply("▶️ Resumed.", mention_author=False)

    # ======================
    # NOW PLAYING
    # ======================
    @commands.hybrid_command(name="nowplaying", aliases=["np"])
    async def nowplaying(self, ctx: commands.Context):
        vc = ctx.guild.voice_client
        if not vc or not vc.current:
            return await ctx.reply("❌ Nothing is playing.", mention_author=False)

        track = vc.current
        embed = discord.Embed(
            title="Now Playing",
            description=f"**{track.title}**",
            color=discord.Color.blurple()
        )
        embed.add_field(name="Duration", value=f"{int(track.length/1000)}s")

        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
