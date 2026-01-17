# cogs/music.py
import discord
from discord.ext import commands
from discord import app_commands
import wavelink
import asyncio
import os
from typing import Optional
from core.player import MusicPlayer
from core.utils import is_youtube_url, is_spotify_url, extract_spotify_id
import config

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # guild_id -> player will be handled by wavelink/guild voice client

    async def ensure_voice(self, ctx_or_inter):
        # accepts either commands.Context or discord.Interaction
        if isinstance(ctx_or_inter, discord.Interaction):
            user = ctx_or_inter.user
            send = ctx_or_inter.response
            ep = True
        else:
            user = ctx_or_inter.author
            send = None
            ep = False

        if not getattr(user, "voice", None) or not user.voice.channel:
            if send:
                await ctx_or_inter.response.send_message("❌ Join a voice channel first.", ephemeral=True)
            else:
                await ctx_or_inter.send("❌ Join a voice channel first.")
            return None

        guild = user.guild if hasattr(user, "guild") else ctx_or_inter.guild
        vc = guild.voice_client
        if not vc:
            # connect using our custom MusicPlayer
            channel = user.voice.channel
            await channel.connect(cls=MusicPlayer)
            vc = guild.voice_client
        return vc

    # ---------- JOIN ----------
    @commands.command(name="join")
    async def join_prefix(self, ctx: commands.Context):
        vc = await self.ensure_voice(ctx)
        if not vc:
            return
        await ctx.send("✅ Joined your voice channel.")

    @app_commands.command(name="join", description="Make the bot join your voice channel")
    async def join_slash(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        vc = await self.ensure_voice(interaction)
        if not vc:
            return
        await interaction.followup.send("✅ Joined your voice channel.", ephemeral=True)

    # ---------- PLAY ----------
    @commands.command(name="play", aliases=["p"])
    async def play_prefix(self, ctx: commands.Context, *, query: str):
        await self._play(ctx, query)

    @app_commands.describe(query="YouTube, Spotify link, or search term")
    @app_commands.command(name="play", description="Play a song (YT/Spotify/name)")
    async def play_slash(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        # create a fake context-like object carrying interaction
        await self._play(interaction, query)

    async def _play(self, ctx_or_inter, query: str):
        is_interaction = isinstance(ctx_or_inter, discord.Interaction)
        if is_interaction:
            interaction = ctx_or_inter
            await interaction.response.defer()
        else:
            ctx = ctx_or_inter

        vc = await self.ensure_voice(ctx_or_inter)
        if not vc:
            return

        # resolve track(s)
        try:
            if is_youtube_url(query):
                tracks = await wavelink.YouTubeTrack.search(query, return_first=False)
            else:
                # treat as search term
                tracks = await wavelink.YouTubeTrack.search(query, return_first=False)
        except Exception:
            if is_interaction:
                await interaction.followup.send("❌ Error searching for track.", ephemeral=True)
            else:
                await ctx.send("❌ Error searching for track.")
            return

        if not tracks:
            if is_interaction:
                await interaction.followup.send("❌ No results found.", ephemeral=True)
            else:
                await ctx.send("❌ No results found.")
            return

        # playlists returned as TrackPlaylist by wavelink
        if isinstance(tracks, wavelink.TrackPlaylist):
            await vc.queue.add_tracks(tracks.tracks)
            msg = f"📂 Added playlist with {len(tracks.tracks)} tracks."
            if is_interaction:
                await interaction.followup.send(msg)
            else:
                await ctx.send(msg)
        else:
            track = tracks[0]
            await vc.queue.put(track)
            msg = f"🎶 Added **{track.title}** to queue."
            if is_interaction:
                await interaction.followup.send(msg)
            else:
                await ctx.send(msg)

        if not vc.playing and not vc.is_paused():
            if not vc.queue.is_empty():
                nxt = await vc.queue.get()
                await vc.play(nxt)

    # ---------- SKIP ----------
    @commands.command(name="skip")
    async def skip_prefix(self, ctx: commands.Context):
        vc = ctx.guild.voice_client
        if not vc or not vc.playing:
            return await ctx.send("❌ Nothing playing.")
        await vc.stop()
        await ctx.send("⏭️ Skipped.")

    @app_commands.command(name="skip", description="Skip current track")
    async def skip_slash(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc or not vc.playing:
            return await interaction.response.send_message("❌ Nothing playing.", ephemeral=True)
        await vc.stop()
        await interaction.response.send_message("⏭️ Skipped.", ephemeral=True)

    # ---------- SKIPTO ----------
    @commands.command(name="skipto")
    async def skipto_prefix(self, ctx: commands.Context, position: int):
        vc: MusicPlayer = ctx.guild.voice_client
        if not vc:
            return await ctx.send("Not connected.")
        if position <= 0:
            return await ctx.send("Position must be >= 1")
        q = vc.queue.as_list()
        if position > len(q):
            return await ctx.send("Position out of range.")
        # remove first (position-1) tracks
        for _ in range(position-1):
            # drop from _list
            q.pop(0)
        # rebuild queue
        vc.queue._list = q
        vc.queue._queue = asyncio.Queue()
        for item in q:
            vc.queue._queue.put_nowait(item)
        # stop current to play next
        await vc.stop()
        await ctx.send(f"⏭ Skipped to position {position}.")

    @app_commands.describe(position="Queue position (1-based)")
    @app_commands.command(name="skipto", description="Skip to a position in the queue")
    async def skipto_slash(self, interaction: discord.Interaction, position: int):
        await interaction.response.defer(ephemeral=True)
        # reuse prefix implementation context
        fake_ctx = interaction
        await self.skipto_prefix.__wrapped__(self, fake_ctx, position)
        await interaction.followup.send(f"⏭ Skipped to {position}", ephemeral=True)

    # ---------- PREVIOUS & NEXT (history navigation) ----------
    @commands.command(name="next")
    async def next_prefix(self, ctx: commands.Context):
        vc: MusicPlayer = ctx.guild.voice_client
        if not vc:
            return await ctx.send("Not connected.")
        if not vc.queue.is_empty():
            await vc.stop()
            return await ctx.send("⏭ Playing next.")
        return await ctx.send("No next track.")

    @commands.command(name="previous")
    async def previous_prefix(self, ctx: commands.Context):
        vc: MusicPlayer = ctx.guild.voice_client
        if not vc:
            return await ctx.send("Not connected.")
        # naive previous: try pop last from history
        if hasattr(vc, "_history") and len(vc._history) >= 1:
            prev = vc._history.pop()
            await vc.queue._list.insert(0, prev)
            await vc.queue._queue.put_nowait(prev)
            await vc.stop()
            return await ctx.send("⏮ Playing previous.")
        return await ctx.send("No previous track available.")

    # ---------- SEEK (forward/backward) ----------
    @commands.command(name="forward")
    async def forward_prefix(self, ctx: commands.Context, seconds: int):
        vc: MusicPlayer = ctx.guild.voice_client
        if not vc or not vc.current_track:
            return await ctx.send("Nothing is playing.")
        pos = vc.position / 1000  # ms -> s
        new_pos = min((vc.current_track.length/1000)-1, pos + seconds)
        await vc.seek(int(new_pos*1000))
        await ctx.send(f"⏩ Forwarded {seconds}s.")

    @commands.command(name="backward")
    async def backward_prefix(self, ctx: commands.Context, seconds: int):
        vc: MusicPlayer = ctx.guild.voice_client
        if not vc or not vc.current_track:
            return await ctx.send("Nothing is playing.")
        pos = vc.position / 1000
        new_pos = max(0, pos - seconds)
        await vc.seek(int(new_pos*1000))
        await ctx.send(f"⏪ Rewinded {seconds}s.")

    # ---------- PAUSE / RESUME ----------
    @commands.command(name="pause")
    async def pause_prefix(self, ctx: commands.Context):
        vc = ctx.guild.voice_client
        if not vc or not vc.playing:
            return await ctx.send("Nothing is playing.")
        await vc.pause()
        await ctx.send("⏸️ Paused.")

    @commands.command(name="resume")
    async def resume_prefix(self, ctx: commands.Context):
        vc = ctx.guild.voice_client
        if not vc:
            return await ctx.send("Not connected.")
        await vc.resume()
        await ctx.send("▶️ Resumed.")

    # ---------- STOP / LEAVE ----------
    @commands.command(name="stop")
    async def stop_prefix(self, ctx: commands.Context):
        vc = ctx.guild.voice_client
        if not vc:
            return await ctx.send("Not connected.")
        vc.queue.clear()
        await vc.stop()
        await vc.disconnect()
        await ctx.send("⏹️ Stopped and left the channel.")

    @commands.command(name="leave")
    async def leave_prefix(self, ctx: commands.Context):
        vc = ctx.guild.voice_client
        if not vc:
            return await ctx.send("Not connected.")
        await vc.disconnect()
        await ctx.send("Left the channel.")

    # ---------- NOW PLAYING ----------
    @commands.command(name="nowplaying", aliases=["np"])
    async def nowplaying_prefix(self, ctx: commands.Context):
        vc = ctx.guild.voice_client
        if not vc or not vc.current_track:
            return await ctx.send("Nothing is playing.")
        tr = vc.current_track
        embed = discord.Embed(title="Now Playing", description=f"**{tr.title}**", color=discord.Color.blurple())
        embed.add_field(name="Author", value=getattr(tr, "author", "Unknown"), inline=True)
        embed.add_field(name="Duration", value=f"{int(tr.length/1000)}s", inline=True)
        await ctx.send(embed=embed)

    # ---------- QUEUE ----------
    @commands.command(name="queue")
    async def queue_prefix(self, ctx: commands.Context):
        vc = ctx.guild.voice_client
        if not vc or vc.queue.is_empty():
            return await ctx.send("Queue is empty.")
        lst = vc.queue.as_list()
        lines = []
        for i, t in enumerate(lst[:15], start=1):
            lines.append(f"`{i}.` {t.title} [{int(t.length/1000)}s]")
        await ctx.send("**Queue (next 15):**\n" + "\n".join(lines))

    # ---------- VOLUME ----------
    @commands.command(name="volume")
    async def volume_prefix(self, ctx: commands.Context, volume: int):
        vc = ctx.guild.voice_client
        if not vc:
            return await ctx.send("Not connected.")
        if volume < 0 or volume > config.MAX_VOLUME:
            return await ctx.send(f"Volume must be between 0 and {config.MAX_VOLUME}.")
        await vc.set_volume(volume)
        await ctx.send(f"🔊 Volume set to {volume}%")

    # Lavalink track end forwarded to player.do_next in bot main

async def setup(bot):
    await bot.add_cog(Music(bot))
