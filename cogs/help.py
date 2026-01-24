# cogs/help.py
import discord
from discord.ext import commands
import config

class HelpView(discord.ui.View):
    def __init__(self, categories: dict):
        super().__init__(timeout=120)
        self.categories = categories
        options = [discord.SelectOption(label=cat, description=f"{len(cmds)} commands") for cat, cmds in categories.items()]
        self.select = discord.ui.Select(placeholder="Select a category", options=options)
        self.select.callback = self._on_select
        self.add_item(self.select)

    async def _on_select(self, interaction: discord.Interaction):
        category = self.select.values[0]
        embed = discord.Embed(title=f"{category} — Commands", color=discord.Color.blurple())
        for cmd, desc in self.categories[category]:
            embed.add_field(name=cmd, value=desc, inline=False)
        await interaction.response.edit_message(embed=embed, view=self)

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    HELP_CATEGORIES = {
        "🎵 Music Playback": [
            (".p / .play <song>", "Play a song (primary: .p)"),
            (".join", "Join your voice channel"),
            (".skip", "Skip current track"),
            (".stop", "Stop and leave"),
        ],
        "📜 Queue & Utility": [
            (".queue", "Show queue"),
            (".nowplaying / .np", "Show current song"),
            (".help", "This menu"),
        ],
        "❤️ Liked Songs": [
            (".like", "Like current song"),
            (".liked", "View your liked songs"),
        ]
    }

    @commands.hybrid_command(name="help", description="Show help menu")
    async def help(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.interaction.response.defer(ephemeral=True)
        embed = discord.Embed(title=f"{config.BOT_NAME} — Help", description="Select a category from the menu below.", color=discord.Color.blurple())
        view = HelpView(self.HELP_CATEGORIES)
        await ctx.reply(embed=embed, view=view, mention_author=False)

async def setup(bot):
    await bot.add_cog(Help(bot))
