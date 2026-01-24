# cogs/lyrics.py
import discord
from discord.ext import commands
import os

GENIUS_TOKEN = os.getenv("GENIUS_TOKEN")

if GENIUS_TOKEN:
    import lyricsgenius
    genius = lyricsgenius.Genius(GENIUS_TOKEN)
else:
    genius = None

class Lyrics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="lyrics", description="Get lyrics for current song or query")
    async def lyrics(self, ctx: commands.Context, *, query: str = None):
        if ctx.interaction:
            await ctx.interaction.response.defer()
        if not genius:
            return await ctx.reply("⚠️ Lyrics service not configured.", mention_author=False)
        if not query:
            vc = ctx.guild.voice_client
            if not vc or not getattr(vc, "current_track", None):
                return await ctx.reply("❌ Provide a query or play a song.", mention_author=False)
            query = getattr(vc.current_track, "title", None)
        try:
            song = genius.search_song(query)
            if not song:
                return await ctx.reply("❌ No lyrics found.", mention_author=False)
            # send first 1900 chars only
            text = song.lyrics
            if len(text) > 1900:
                text = text[:1900] + "\n... (truncated)"
            await ctx.reply(f"**{song.title} — {song.artist}**\n\n{text}", mention_author=False)
        except Exception:
            await ctx.reply("❌ Lyrics lookup failed.", mention_author=False)

async def setup(bot):
    await bot.add_cog(Lyrics(bot))
