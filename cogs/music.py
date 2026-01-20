# cogs/music.py
import discord
from discord.ext import commands
import wavelink

from core.player import MusicPlayer


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def ensure_voice(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.reply("❌ Join a voice channel first.", mention_author=False)
            return None

        vc = ctx.guild.voice_client
        if not vc:
            await ctx.author.voice.channel.connect(cls=MusicPlayer)
            vc = ctx.guild.voice_client
        return vc

    # ================= JOIN =================
    @commands.hybrid_command(name="join", description="Join your voice channel")
    async def join(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.interaction.response.defer(ephemeral=True)

        vc = await self.ensure_voice(ctx)
        if vc:
            await ctx.reply("✅ Joined your voice channel.", mention_author=False)

    # ================= PLAY (.p PRIMARY) =================
    @commands.hybrid_command(
        name="p",
        aliases=["play"],
        description="Play a song from YouTube"
    )
    async def p(self, ctx: commands.Context, *, query: str):
        if ctx.interaction:
            await ctx.interaction.response.defer()

        vc = await self.ensure_voice(ctx)
        if not vc:
            return

        tracks = await wavelink.YouTubeTrack.search(query)
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

    # ================= SKIP =================
    @commands.hybrid_command(name="skip", description="Skip current track")
    async def skip(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.interaction.response.defer(ephemeral=True)

        vc = ctx.guild.voice_client
        if not vc or not vc.playing:
            return await ctx.reply("❌ Nothing is playing.", mention_author=False)

        await vc.stop()
        await ctx.reply("⏭️ Skipped.", mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
