# cogs/music.py
import discord
from discord.ext import commands
import wavelink

from core.player import MusicPlayer
from core.utils import is_youtube_url, is_spotify_url
import config

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

    @commands.hybrid_command(name="join", description="Join your voice channel")
    async def join(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.interaction.response.defer(ephemeral=True)
        vc = await self.ensure_voice(ctx)
        if vc:
            await ctx.reply("✅ Joined your voice channel.", mention_author=False)

    @commands.hybrid_command(name="p", aliases=["play"], description="Play a song from YouTube or search")
    async def p(self, ctx: commands.Context, *, query: str):
        if ctx.interaction:
            await ctx.interaction.response.defer()
        vc = await self.ensure_voice(ctx)
        if not vc:
            return

        # Basic YT search; wavelink handles URLs too
        try:
            tracks = await wavelink.YouTubeTrack.search(query, return_first=False)
        except Exception:
            return await ctx.reply("❌ Search error.", mention_author=False)

        if not tracks:
            return await ctx.reply("❌ No results found.", mention_author=False)

        # if playlist returned
        if isinstance(tracks, wavelink.TrackPlaylist):
            vc.queue.add_tracks(tracks.tracks)
            await ctx.reply(f"📂 Added playlist ({len(tracks.tracks)} tracks) to queue.", mention_author=False)
        else:
            track = tracks[0]
            await vc.queue.put(track)
            await ctx.reply(f"🎶 Added **{track.title}** to the queue", mention_author=False)

        if not vc.playing:
            await vc.play(await vc.queue.get())

    @commands.hybrid_command(name="skip", description="Skip current track")
    async def skip(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.interaction.response.defer(ephemeral=True)
        vc = ctx.guild.voice_client
        if not vc or not vc.playing:
            return await ctx.reply("❌ Nothing playing.", mention_author=False)
        await vc.stop()
        await ctx.reply("⏭️ Skipped.", mention_author=False)

    @commands.hybrid_command(name="stop", description="Stop playback and leave")
    async def stop(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.interaction.response.defer(ephemeral=True)
        vc = ctx.guild.voice_client
        if not vc:
            return await ctx.reply("❌ Not connected.", mention_author=False)
        vc.queue.clear()
        await vc.stop()
        await vc.disconnect()
        await ctx.reply("⏹️ Stopped and left the channel.", mention_author=False)

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

    @commands.hybrid_command(name="nowplaying", aliases=["np"], description="Show current song")
    async def nowplaying(self, ctx: commands.Context):
        vc = ctx.guild.voice_client
        if not vc or not vc.current_track:
            return await ctx.reply("❌ Nothing is playing.", mention_author=False)
        tr = vc.current_track
        embed = discord.Embed(title="Now Playing", description=f"**{tr.title}**", color=discord.Color.blurple())
        embed.add_field(name="Author", value=getattr(tr, "author", "Unknown"), inline=True)
        embed.add_field(name="Duration", value=f"{int(tr.length/1000)}s", inline=True)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(name="queue", description="Show next tracks")
    async def queue(self, ctx: commands.Context):
        vc = ctx.guild.voice_client
        if not vc or vc.queue.is_empty():
            return await ctx.reply("Queue is empty.", mention_author=False)
        lst = vc.queue.as_list()
        lines = [f"`{i+1}.` {t.title} [{int(getattr(t, 'length', 0)/1000)}s]" for i, t in enumerate(lst[:15])]
        await ctx.reply("**Queue (next 15):**\n" + "\n".join(lines), mention_author=False)


async def setup(bot):
    await bot.add_cog(Music(bot))
