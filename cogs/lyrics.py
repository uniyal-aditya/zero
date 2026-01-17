# cogs/lyrics.py
import discord
from discord.ext import commands
from discord import app_commands
import lyricsgenius
import os

class Lyrics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        token = os.getenv("GENIUS_TOKEN")
        self.genius = lyricsgenius.Genius(
            token,
            skip_non_songs=True,
            excluded_terms=["(Remix)", "(Live)"],
            remove_section_headers=True
        ) if token else None

    async def fetch_lyrics(self, query: str):
        if not self.genius:
            return None
        song = self.genius.search_song(query)
        if not song or not song.lyrics:
            return None
        return song

    # PREFIX COMMAND
    @commands.command(name="lyrics")
    async def lyrics_prefix(self, ctx: commands.Context):
        vc = ctx.guild.voice_client
        if not vc or not vc.current_track:
            return await ctx.send("❌ No song is currently playing.")

        query = vc.current_track.title
        await ctx.send("🔍 Searching lyrics...")

        song = await self.fetch_lyrics(query)
        if not song:
            return await ctx.send("❌ Lyrics not found.")

        embed = discord.Embed(
            title=f"🎵 Lyrics — {song.title}",
            description=song.lyrics[:4000],
            color=discord.Color.purple()
        )
        embed.set_footer(text="Powered by Genius")
        await ctx.send(embed=embed)

    # SLASH COMMAND
    @app_commands.command(name="lyrics", description="Get lyrics of the currently playing song")
    async def lyrics_slash(self, interaction: discord.Interaction):
        await interaction.response.defer()

        vc = interaction.guild.voice_client
        if not vc or not vc.current_track:
            return await interaction.followup.send("❌ No song is currently playing.", ephemeral=True)

        query = vc.current_track.title
        song = await self.fetch_lyrics(query)

        if not song:
            return await interaction.followup.send("❌ Lyrics not found.", ephemeral=True)

        embed = discord.Embed(
            title=f"🎵 Lyrics — {song.title}",
            description=song.lyrics[:4000],
            color=discord.Color.purple()
        )
        embed.set_footer(text="Powered by Genius")
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Lyrics(bot))
