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
import requests

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.players = {}  # guild_id -> MusicPlayer

    # Helper to get or create a player for a guild
    async def get_player(self, guild: discord.Guild) -> MusicPlayer:
        vc = guild.voice_client
        if vc and isinstance(vc, MusicPlayer):
            return vc

        # create new player by connecting to node
        node = wavelink.NodePool.get_node()
        player = MusicPlayer(bot=self.bot, guild=guild, node=node)
        self.bot.players[guild.id] = player
        return player

    async def ensure_voice(self, interaction: discord.Interaction) -> Optional[MusicPlayer]:
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("Join a voice channel first.", ephemeral=True)
            return None

        guild = interaction.guild
        vc = guild.voice_client
        if not vc:
            # connect using wavelink Player
            channel = interaction.user.voice.channel
            await channel.connect(cls=MusicPlayer)
            vc = guild.voice_client

        return vc

    @app_commands.command(name="join", description="Make the bot join your voice channel")
    async def join(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        vc = await self.ensure_voice(interaction)
        if not vc:
            return
        await interaction.followup.send("✅ Joined your voice channel.", ephemeral=True)

    @app_commands.describe(query="YouTube link, Spotify link, or search term")
    @app_commands.command(name="play", description="Play a song by link or search")
    async def play(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        vc = await self.ensure_voice(interaction)
        if not vc:
            return

        # Resolve query: youtube or spotify or search
        if is_youtube_url(query):
            # let wavelink handle youtube url
            tracks = await wavelink.YouTubeTrack.search(query, return_first=False)
            if not tracks:
                await interaction.followup.send("No results found for that YouTube link.")
                return
            # if playlist, tracks might be a Playlist object
            if isinstance(tracks, wavelink.TrackPlaylist):
                await vc.queue.add_tracks(tracks.tracks)
                await interaction.followup.send(f"📂 Added playlist with {len(tracks.tracks)} tracks.")
            else:
                await vc.queue.put(tracks[0])
                await interaction.followup.send(f"🎶 Added **{tracks[0].title}** to queue.")
        elif is_spotify_url(query):
            # Spotify link: try to resolve via Spotify API if credentials present, otherwise search YouTube
            spotify_id = extract_spotify_id(query)
            typ, sid = spotify_id
            if os.getenv("SPOTIFY_CLIENT_ID") and os.getenv("SPOTIFY_CLIENT_SECRET"):
                # Minimal Spotify metadata fetch (Client Credentials)
                token = self._get_spotify_token()
                if token:
                    if typ == "track":
                        meta = self._get_spotify_track(token, sid)
                        if meta:
                            # search YouTube with artist - title
                            q = f"{meta['artists'][0]['name']} - {meta['name']}"
                            tracks = await wavelink.YouTubeTrack.search(q, return_first=True)
                            if not tracks:
                                await interaction.followup.send("Could not resolve Spotify track to YouTube.")
                                return
                            await vc.queue.put(tracks)
                            await interaction.followup.send(f"🎶 Added **{tracks.title}** (from Spotify link)")
                            if not vc.playing:
                                await vc.play(await vc.queue.get())
                            return
                    # playlist/album handling can be added similarly
            # fallback: search YouTube using raw link text
            tracks = await wavelink.YouTubeTrack.search(query, return_first=False)
            if not tracks:
                # as last resort, search by the textual portion after last slash
                q = query.split("/")[-1]
                tracks = await wavelink.YouTubeTrack.search(q, return_first=False)
            if not tracks:
                await interaction.followup.send("Couldn't resolve Spotify link.")
                return
            # pick first track
            await vc.queue.put(tracks[0])
            await interaction.followup.send(f"🎶 Added **{tracks[0].title}** (resolved from Spotify link)")
        else:
            # treat as search term
            found = await wavelink.YouTubeTrack.search(query, return_first=False)
            if not found:
                await interaction.followup.send("No results found.")
                return
            track = found[0]
            await vc.queue.put(track)
            await interaction.followup.send(f"🎶 Added **{track.title}** to queue")

        # auto-play if not playing
        if not vc.playing and not vc.is_paused():
            if not vc.queue.is_empty():
                next_track = await vc.queue.get()
                await vc.play(next_track)

    @app_commands.command(name="skip", description="Skip current track")
    async def skip(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        vc = interaction.guild.voice_client
        if not vc or not vc.playing:
            await interaction.followup.send("❌ Nothing is playing.", ephemeral=True)
            return
        await vc.stop()
        await interaction.followup.send("⏭️ Skipped.", ephemeral=True)

    @app_commands.command(name="pause", description="Pause playback")
    async def pause(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc or not vc.playing:
            await interaction.response.send_message("❌ Nothing playing.", ephemeral=True)
            return
        await vc.pause()
        await interaction.response.send_message("⏸️ Paused.", ephemeral=True)

    @app_commands.command(name="resume", description="Resume playback")
    async def resume(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc:
            await interaction.response.send_message("❌ Bot not connected.", ephemeral=True)
            return
        await vc.resume()
        await interaction.response.send_message("▶️ Resumed.", ephemeral=True)

    @app_commands.command(name="stop", description="Stop playback and clear queue")
    async def stop(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc:
            await interaction.response.send_message("❌ Not connected.", ephemeral=True)
            return
        vc.queue.clear()
        await vc.stop()
        await vc.disconnect()
        await interaction.response.send_message("⏹️ Stopped and left the voice channel.")

    @app_commands.command(name="nowplaying", description="Show current playing song")
    async def nowplaying(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc or not vc.current_track:
            await interaction.response.send_message("❌ Nothing is playing.", ephemeral=True)
            return
        track = vc.current_track
        embed = discord.Embed(title="Now Playing", description=f"**{track.title}**", color=discord.Color.blurple())
        embed.add_field(name="Duration", value=str(track.length/1000) + "s", inline=True)
        embed.add_field(name="Requested by", value="N/A", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="queue", description="Show the queue")
    async def queue_cmd(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc or vc.queue.is_empty():
            await interaction.response.send_message("Queue is empty.", ephemeral=True)
            return
        lst = vc.queue.as_list()
        lines = []
        for i, t in enumerate(lst[:10], start=1):
            lines.append(f"`{i}.` {t.title} [{int(t.length/1000)}s]")
        content = "\n".join(lines)
        await interaction.response.send_message(f"**Queue (next 10):**\n{content}")

    @app_commands.describe(volume="0-200")
    @app_commands.command(name="volume", description="Set player volume")
    async def volume(self, interaction: discord.Interaction, volume: int):
        vc = interaction.guild.voice_client
        if not vc:
            await interaction.response.send_message("Not connected.", ephemeral=True)
            return
        if volume < 0 or volume > 200:
            await interaction.response.send_message("Volume must be between 0 and 200.", ephemeral=True)
            return
        await vc.set_volume(volume)
        await interaction.response.send_message(f"🔊 Volume set to {volume}%")

    # --- Optional simple Spotify helper
    def _get_spotify_token(self):
        """Client credentials flow"""
        cid = os.getenv("SPOTIFY_CLIENT_ID")
        secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        if not cid or not secret:
            return None
        token_url = "https://accounts.spotify.com/api/token"
        r = requests.post(token_url, data={"grant_type": "client_credentials"}, auth=(cid, secret))
        if r.status_code != 200:
            return None
        return r.json().get("access_token")

    def _get_spotify_track(self, token, track_id):
        url = f"https://api.spotify.com/v1/tracks/{track_id}"
        r = requests.get(url, headers={"Authorization": f"Bearer {token}"})
        if r.status_code != 200:
            return None
        return r.json()


async def setup(bot):
    await bot.add_cog(Music(bot))
