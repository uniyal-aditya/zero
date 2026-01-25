# cogs/help.py
import discord
from discord.ext import commands
from discord import app_commands

HELP_CATEGORIES = {
    "Music (Free)": [
        (".p / /p <query>", "Play a song (YouTube search or link)"),
        (".skip", "Skip current track"),
        (".queue", "Show queue"),
        (".nowplaying / .np", "Show current track"),
        (".pause", "Pause playback"),
        (".resume", "Resume playback"),
    ],
    "Music (Premium)": [
        (".loop <off/track/queue>", "Loop modes (Premium)"),
        (".shuffle", "Shuffle queue (Premium)"),
        (".skipto <pos>", "Skip to queue position (Premium)"),
        (".247 on/off", "24/7 stay in voice (Premium)"),
    ],
    "Utility": [
        (".volume <0-200>", "Set playback volume"),
        (".help", "Show help menu"),
    ],
    "Liked / Playlists": [
        (".like", "Like current song"),
        (".liked", "View liked songs"),
        (".playlist create <name>", "Create a personal playlist"),
    ],
}

class HelpView(discord.ui.View):
    def __init__(self, author_id: int):
        super().__init__(timeout=120)
        self.author_id = author_id

        options = [discord.SelectOption(label=k, description=f"{len(v)} commands") for k, v in HELP_CATEGORIES.items()]
        self.select = discord.ui.Select(placeholder="Choose a category", options=options, min_values=1, max_values=1)
        self.select.callback = self._callback
        self.add_item(self.select)

    async def _callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("This help menu isn't for you.", ephemeral=True)
        cat = self.select.values[0]
        embed = discord.Embed(title=f"{cat} — Commands", color=discord.Color.blurple())
        for cmd, desc in HELP_CATEGORIES[cat]:
            embed.add_field(name=cmd, value=desc, inline=False)
        await interaction.response.edit_message(embed=embed, view=self)

class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="help", description="Show help menu with categories")
    async def help(self, ctx: commands.Context):
        embed = discord.Embed(title=f"{self.bot.user.name} — Help", description="Select a category from the menu below.", color=discord.Color.blurple())
        embed.set_footer(text="Premium commands are labeled in the Music (Premium) category.")
        view = HelpView(ctx.author.id)
        if ctx.interaction:
            await ctx.interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        else:
            await ctx.reply(embed=embed, view=view, mention_author=False)

async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))
