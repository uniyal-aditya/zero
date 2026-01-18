# cogs/help.py
import discord
from discord.ext import commands
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

    @commands.hybrid_command(name="help")
    async def help(self, ctx: commands.Context, *, category: str = None):
        """
        Unified help command (prefix + slash)
        """

        # Main help
        if not category:
            embed = discord.Embed(
                title=f"{config.BOT_NAME} — Help",
                description=(
                    "Use `.help <category>` or `/help <category>` to view details.\n\n"
                    "**Available Categories:**\n"
                    + "\n".join(self.HELP_CATEGORIES.keys())
                ),
                color=discord.Color.blurple()
            )
            embed.set_footer(text="Zero™ • polished help panel")
            await ctx.reply(embed=embed)
            return

        # Category help
        category = category.title()
        if category not in self.HELP_CATEGORIES:
            await ctx.reply("❌ Unknown category. Use `.help` to list categories.")
            return

        embed = discord.Embed(
            title=f"{category} — Commands",
            color=discord.Color.blurple()
        )

        for cmd, desc in self.HELP_CATEGORIES[category]:
            embed.add_field(name=cmd, value=desc, inline=False)

        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(Help(bot))
