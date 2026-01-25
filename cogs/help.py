# cogs/help.py
import discord
from discord.ext import commands
from discord import app_commands
import config

class HelpView(discord.ui.View):
    def __init__(self, categories):
        super().__init__(timeout=180)
        self.categories = categories
        options = []
        for k, v in categories.items():
            has_premium = any(it.get("premium", False) for it in v)
            label = f"{k} {'(PREMIUM)' if has_premium else ''}".strip()
            options.append(discord.SelectOption(label=label, description=f"{len(v)} commands"))

        options.insert(0, discord.SelectOption(label="All Commands", description="Show all commands"))
        self.select = discord.ui.Select(placeholder="Select a category", min_values=1, max_values=1, options=options)
        self.select.callback = self.callback
        self.add_item(self.select)

    async def callback(self, interaction: discord.Interaction):
        chosen = self.select.values[0]
        if chosen == "All Commands":
            embed = discord.Embed(title=f"{config.BOT_NAME} — All Commands", color=discord.Color.blurple())
            free_lines = []
            premium_lines = []
            for k, v in self.categories.items():
                for item in v:
                    line = f"**{item['cmd']}** — {item['desc']}"
                    if item.get("premium"):
                        premium_lines.append(line)
                    else:
                        free_lines.append(line)
            if free_lines:
                embed.add_field(name="Free", value="\n".join(free_lines), inline=False)
            if premium_lines:
                embed.add_field(name="Premium", value="\n".join(premium_lines), inline=False)
            await interaction.response.edit_message(embed=embed, view=self)
            return
        # else find matching category
        cat_name = chosen.split(" (")[0]
        items = self.categories.get(cat_name, [])
        embed = discord.Embed(title=f"{cat_name} — Commands", color=discord.Color.blurple())
        for it in items:
            name = it["cmd"]
            if it.get("premium"):
                name = f"💎 {name}"
            embed.add_field(name=name, value=it["desc"], inline=False)
        await interaction.response.edit_message(embed=embed, view=self)

class Help(commands.Cog):
    HELP_CATEGORIES = {
        "Music Playback": [
            {"cmd": ".p / .play <song>", "desc": "Play a song", "premium": False},
            {"cmd": ".join", "desc": "Join VC", "premium": False},
            {"cmd": ".skip", "desc": "Skip current track", "premium": False},
            {"cmd": ".nowplaying", "desc": "Show current track", "premium": False},
        ],
        "Queue & Navigation": [
            {"cmd": ".queue", "desc": "Show queue", "premium": False},
            {"cmd": ".skipto <pos>", "desc": "Skip to position", "premium": True},
            {"cmd": ".shuffle", "desc": "Shuffle queue", "premium": True},
            {"cmd": ".loop <off|track|queue>", "desc": "Loop mode", "premium": True},
        ],
        "Liked Songs": [
            {"cmd": ".like", "desc": "Like a song", "premium": False},
            {"cmd": ".liked", "desc": "Show liked songs", "premium": False},
        ],
        "Premium": [
            {"cmd": ".buy_premium", "desc": "Guild owner: buy premium for the server", "premium": True},
            {"cmd": ".grant_premium <guild_id>", "desc": "Owner: grant premium", "premium": True},
        ],
        "Utility": [
            {"cmd": ".help", "desc": "Show this help", "premium": False},
            {"cmd": ".lyrics <query>", "desc": "Get lyrics", "premium": False},
        ]
    }

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_prefix(self, ctx: commands.Context):
        embed = discord.Embed(title=f"{config.BOT_NAME} — Help", color=discord.Color.blurple())
        embed.description = "Select a category from the dropdown below. Premium commands are marked."
        view = HelpView(self.HELP_CATEGORIES)
        await ctx.reply(embed=embed, view=view, mention_author=False)

    @app_commands.command(name="help", description="Show help")
    async def help_slash(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(title=f"{config.BOT_NAME} — Help", color=discord.Color.blurple())
        embed.description = "Select a category from the dropdown below. Premium commands are marked."
        view = HelpView(self.HELP_CATEGORIES)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Help(bot))
