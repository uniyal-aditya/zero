# cogs/help.py
import discord
from discord.ext import commands
from discord import app_commands
import config

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    HELP_CATEGORIES = {
    "🎵 Music Playback": [
        (".play <song/link>", "Play a song or playlist"),
        (".pause", "Pause playback"),
        (".resume", "Resume playback"),
        (".stop", "Stop music and clear queue"),
        (".join", "Join your voice channel"),
        (".leave", "Leave the voice channel"),
    ],

    "⏭ Queue & Navigation": [
        (".queue", "Show current queue"),
        (".skip", "Skip current track"),
        (".skipto <pos>", "Skip to a queue position"),
        (".next", "Play next track"),
        (".previous", "Play previous track"),
        (".forward <sec>", "Seek forward"),
        (".backward <sec>", "Seek backward"),
    ],

    "🔁 Modes": [
        (".loop off/track/queue", "Loop modes"),
        (".autoplay on/off", "Automatic song suggestions"),
    ],

    "❤️ Liked Songs": [
        (".like", "Like current song"),
        (".liked", "View your liked songs"),
        (".liked play", "Play liked songs"),
        (".liked shuffle", "Shuffle liked songs"),
        (".liked remove <id>", "Remove liked song"),
        (".liked clear", "Clear liked songs"),
        (".liked count", "Total liked songs"),
        (".liked recent", "Recently liked songs"),
    ],

    "💎 Premium": [
        (".247 on/off", "24/7 mode (Premium)"),
        (".filter <name>", "Advanced audio filters"),
        (".recommend", "Smart recommendations"),
    ],

    "⚙ Utility": [
        (".nowplaying", "Show current song"),
        (".lyrics", "Get lyrics"),
        (".ping", "Bot latency"),
        (".help", "Show help menu"),
    ],
}


    @commands.command(name="help")
    async def help_prefix(self, ctx: commands.Context, category: str = None):
        if not category:
            embed = discord.Embed(title=f"{config.BOT_NAME} — Help", color=discord.Color.blurple())
            embed.description = "Use `.help <category>` to view details. Categories available:\n\n" + ", ".join(self.HELP_CATEGORIES.keys())
            embed.set_footer(text="Zero™ • polished help panel")
            return await ctx.send(embed=embed)
        category = category.title()
        if category not in self.HELP_CATEGORIES:
            return await ctx.send("Unknown category. Use `.help` to list categories.")
        embed = discord.Embed(title=f"{category} — Commands", color=discord.Color.blurple())
        for cmd, desc in self.HELP_CATEGORIES[category]:
            embed.add_field(name=cmd, value=desc, inline=False)
        await ctx.send(embed=embed)

    @app_commands.command(name="help", description="Show bot help with categories")
    async def help_slash(self, interaction: discord.Interaction, category: str = None):
        await interaction.response.defer(ephemeral=True)
        if not category:
            embed = discord.Embed(title=f"{config.BOT_NAME} — Help", color=discord.Color.blurple())
            embed.description = "Use `/help <category>` to view details. Categories available:\n\n" + ", ".join(self.HELP_CATEGORIES.keys())
            embed.set_footer(text="Zero™ • polished help panel")
            return await interaction.followup.send(embed=embed, ephemeral=True)
        category = category.title()
        if category not in self.HELP_CATEGORIES:
            return await interaction.followup.send("Unknown category. Use `/help` to list categories.", ephemeral=True)
        embed = discord.Embed(title=f"{category} — Commands", color=discord.Color.blurple())
        for cmd, desc in self.HELP_CATEGORIES[category]:
            embed.add_field(name=cmd, value=desc, inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Help(bot))
