# cogs/music.py
import discord
from discord.ext import commands
from discord import app_commands
import wavelink
import asyncio
from typing import Optional

from core.player import MusicPlayer
from core.utils import is_youtube_url
import config

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def ensure_voice(self, ctx_or_inter):
        # works for both prefix Context and Interaction (we will use separate commands)
        if isinstance(ctx_or_inter, discord.Interaction):
            user = ctx_or_inter.user
            if not getattr(user, "voice", None) or not user.voice:
                await ctx_or_inter.response.send_message("❌ Join a voice channel first.", ephemeral=True)
                return None
            guild = ctx_or_inter.guild
            vc = guild.voice_client
            if not vc:
                await user.voice.channel.connect(cls=MusicPlayer)
                vc = guild.voice_client
            return vc
        else:
            ctx = ctx_or_inter
            user = ctx.author
            if not getattr(user, "voice", None) or not user.voice:
                await ctx.reply("❌ Join a voice channel first.", mention_author=False)
                return None
            vc = ctx.guild.voice_client
            if not vc:
                await user.voice.channel.connect(cls=MusicPlayer)
                vc = ctx.guild.voice_client
            return vc

    # JOIN
    @commands.command(name="join")
    async def join_prefix(self, ctx: commands.Context):
        vc = await self.ensure_voice(ctx)
        if not vc:
            return
        await ctx.reply("✅ Joined your voice channel.", mention_author=False)

    @app_commands.command(name="join", description="Join your voice channel")
    async def join_slash(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        vc = await self.ensure_voice(interaction)
        if not vc:
            return
        await interaction.followup.send("✅ Joined your voice channel.", ephemeral=True)

    # PLAY (prefix .p and slash /play)
    @commands.command(name="p", aliases=["play"])
    async def play_prefix(self, ctx: commands.Context, *, query: str):
        vc = await self.ensure_voice(ctx)
        if not vc:
            return
        await self._play_prefix(ctx, query)

    @app_commands.command(name="play", description="Play a song (YT link or search)")
    @app_commands.describe(query="YouTube link or search query")
    async def play_slash(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        vc = await self.ensure_voice(interaction)
        if not vc:
            return
        # delegate to same logic but using followup messages
        await self._play_interaction(interaction, vc, query)

    async def _resolve_tracks(self, query: str):
        # basic: always use YouTubeTrack.search() (wavelink supports ytdl lookups)
        try:
            tracks = await wavelink.YouTubeTrack.search(query, return_first=False)
            return tracks
        except Exception:
            return None

    async def _play_prefix(self, ctx: commands.Context, query: str):
        vc = ctx.guild.voice_client
        tracks = await self._resolve_tracks(query)
        if not tracks:
            return await ctx.reply("❌ No results found.", mention_author=False)
        if isinstance(tracks, wavelink.TrackPlaylist):
            # playlist
            for t in tracks.tracks:
                await vc.queue.put(t)
            await ctx.reply(f"📂 Added playlist ({len(tracks.tracks)} tracks).", mention_author=False)
        else:
            track = tracks[0]
            await vc.queue.put(track)
            await ctx.reply(f"🎶 Added **{track.title}**", mention_author=False)
        # if nothing playing start
        if not vc.is_playing() and not vc.is_paused():
            if not vc.queue.is_empty():
                nxt = await vc.queue.get()
                await vc.play(nxt)

    async def _play_interaction(self, interaction: discord.Interaction, vc, query: str):
        tracks = await self._resolve_tracks(query)
        if not tracks:
            return await interaction.followup.send("❌ No results found.", ephemeral=True)
        if isinstance(tracks, wavelink.TrackPlaylist):
            for t in tracks.tracks:
                await vc.queue.put(t)
            await interaction.followup.send(f"📂 Added playlist ({len(tracks.tracks)} tracks).", ephemeral=True)
        else:
            track = tracks[0]
            await vc.queue.put(track)
            await interaction.followup.send(f"🎶 Added **{track.title}**", ephemeral=True)
        if not vc.is_playing() and not vc.is_paused():
            if not vc.queue.is_empty():
                nxt = await vc.queue.get()
                await vc.play(nxt)

    # SKIP
    @commands.command(name="skip")
    async def skip_prefix(self, ctx: commands.Context):
        vc = ctx.guild.voice_client
        if not vc or not vc.is_playing():
            return await ctx.reply("❌ Nothing playing.", mention_author=False)
        await vc.stop()
        await ctx.reply("⏭ Skipped.", mention_author=False)

    @app_commands.command(name="skip", description="Skip current track")
    async def skip_slash(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc or not vc.is_playing():
            return await interaction.response.send_message("❌ Nothing playing.", ephemeral=True)
        await vc.stop()
        await interaction.response.send_message("⏭ Skipped.", ephemeral=True)

    # SKIPTO (premium)
    @commands.command(name="skipto")
    async def skipto_prefix(self, ctx: commands.Context, position: int):
        vc: MusicPlayer = ctx.guild.voice_client
        if not vc:
            return await ctx.reply("Not connected.", mention_author=False)
        if position <= 0:
            return await ctx.reply("Position must be >= 1", mention_author=False)
        q = vc.queue.as_list()
        if position > len(q):
            return await ctx.reply("Position out of range.", mention_author=False)
        # drop first pos-1 tracks
        for _ in range(position-1):
            try:
                q.pop(0)
            except Exception:
                pass
        vc.queue._list = q
        vc.queue._queue = asyncio.Queue()
        for item in q:
            await vc.queue._queue.put(item)
        await vc.stop()
        await ctx.reply(f"⏭ Skipped to {position}", mention_author=False)

    # NOW PLAYING
    @commands.command(name="nowplaying", aliases=["np"])
    async def nowplaying_prefix(self, ctx: commands.Context):
        vc = ctx.guild.voice_client
        if not vc or not getattr(vc, "current_track", None):
            return await ctx.reply("Nothing is playing.", mention_author=False)
        tr = vc.current_track
        embed = discord.Embed(title="Now Playing", description=f"**{tr.title}**", color=discord.Color.blurple())
        embed.add_field(name="Author", value=getattr(tr, "author", "Unknown"), inline=True)
        embed.add_field(name="Duration", value=f"{int(getattr(tr, 'length', 0)/1000)}s", inline=True)
        await ctx.reply(embed=embed, mention_author=False)

    # QUEUE
    @commands.command(name="queue")
    async def queue_prefix(self, ctx: commands.Context):
        vc = ctx.guild.voice_client
        if not vc or vc.queue.is_empty():
            return await ctx.reply("Queue is empty.", mention_author=False)
        lst = vc.queue.as_list()
        lines = []
        for i, t in enumerate(lst[:15], start=1):
            lines.append(f"`{i}.` {t.title} [{int(getattr(t, 'length', 0)/1000)}s]")
        await ctx.reply("**Queue (next 15):**\n" + "\n".join(lines), mention_author=False)

    # PAUSE / RESUME / STOP / LEAVE
    @commands.command(name="pause")
    async def pause_prefix(self, ctx: commands.Context):
        vc = ctx.guild.voice_client
        if not vc or not vc.is_playing():
            return await ctx.reply("Nothing playing.", mention_author=False)
        await vc.pause()
        await ctx.reply("⏸ Paused.", mention_author=False)

    @commands.command(name="resume")
    async def resume_prefix(self, ctx: commands.Context):
        vc = ctx.guild.voice_client
        if not vc:
            return await ctx.reply("Not connected.", mention_author=False)
        await vc.resume()
        await ctx.reply("▶ Resumed.", mention_author=False)

    @commands.command(name="stop")
    async def stop_prefix(self, ctx: commands.Context):
        vc = ctx.guild.voice_client
        if not vc:
            return await ctx.reply("Not connected.", mention_author=False)
        vc.queue.clear()
        await vc.stop()
        await vc.disconnect()
        await ctx.reply("⏹ Stopped and left the channel.", mention_author=False)

    @commands.command(name="leave")
    async def leave_prefix(self, ctx: commands.Context):
        vc = ctx.guild.voice_client
        if not vc:
            return await ctx.reply("Not connected.", mention_author=False)
        await vc.disconnect()
        await ctx.reply("Left the channel.", mention_author=False)

    # SEEK forward/backward
    @commands.command(name="forward")
    async def forward_prefix(self, ctx: commands.Context, seconds: int):
        vc = ctx.guild.voice_client
        if not vc or not getattr(vc, "current_track", None):
            return await ctx.reply("Nothing is playing.", mention_author=False)
        pos = getattr(vc, "position", 0) / 1000
        new_pos = min((vc.current_track.length / 1000) - 1, pos + seconds)
        await vc.seek(int(new_pos * 1000))
        await ctx.reply(f"⏩ Forwarded {seconds}s.", mention_author=False)

    @commands.command(name="backward")
    async def backward_prefix(self, ctx: commands.Context, seconds: int):
        vc = ctx.guild.voice_client
        if not vc or not getattr(vc, "current_track", None):
            return await ctx.reply("Nothing is playing.", mention_author=False)
        pos = getattr(vc, "position", 0) / 1000
        new_pos = max(0, pos - seconds)
        await vc.seek(int(new_pos * 1000))
        await ctx.reply(f"⏪ Rewinded {seconds}s.", mention_author=False)

    # LOOP
    @commands.command(name="loop")
    async def loop_prefix(self, ctx: commands.Context, mode: str):
        """
        mode: off | track | queue
        """
        vc: MusicPlayer = ctx.guild.voice_client
        if not vc:
            return await ctx.reply("Not connected.", mention_author=False)
        mode = mode.lower()
        if mode not in ("off", "track", "queue"):
            return await ctx.reply("Invalid mode. Use off|track|queue", mention_author=False)
        vc.loop_mode = mode
        await ctx.reply(f"Loop mode set to {mode}", mention_author=False)

async def setup(bot):
    await bot.add_cog(Music(bot))
