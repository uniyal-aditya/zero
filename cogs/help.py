# cogs/help.py
import discord
from discord.ext import commands
import config

"""
Enhanced Help Cog
- Interactive select menu listing categories
- Separates Free and Premium commands
- Works as both prefix (.help) and slash (/help)
- Slash responses are ephemeral; prefix responses are normal channel messages
"""

class HelpView(discord.ui.View):
    def __init__(self, categories: dict, ephemeral: bool):
        super().__init__(timeout=180)
        self.categories = categories
        self.ephemeral = ephemeral

        # Build select options. Show label with FREE / PREMIUM marker.
        options = []
        for cat, items in categories.items():
            # determine if category contains any premium commands
            has_premium = any(it.get("premium", False) for it in items)
            label = f"{cat} {'(PREMIUM)' if has_premium else '(FREE)'}"
            desc = f"{len(items)} commands"
            options.append(discord.SelectOption(label=label, description=desc))

        # Add "All Commands" option
        options.insert(0, discord.SelectOption(label="All Commands (FREE + PREMIUM)", description="Show every command"))

        self.select = discord.ui.Select(placeholder="Select a category", min_values=1, max_values=1, options=options)
        self.select.callback = self.select_callback
        self.add_item(self.select)

    async def select_callback(self, interaction: discord.Interaction):
        # selected label might contain the suffix (PREMIUM/FREE), normalize
        chosen = self.select.values[0]
        if chosen.startswith("All Commands"):
            embed = discord.Embed(title=f"{config.BOT_NAME} — All Commands", color=discord.Color.blurple())
            embed.description = "All available commands grouped by Free / Premium."
            embed.set_footer(text=f"{config.BOT_NAME} • Select to view other categories")
            # Add Free then Premium sections
            free_lines = []
            premium_lines = []
            for cat, items in self.categories.items():
                for it in items:
                    line = f"**{it['cmd']}** — {it['desc']}"
                    if it.get("premium", False):
                        premium_lines.append(line)
                    else:
                        free_lines.append(line)
            if free_lines:
                embed.add_field(name="🟦 Free Commands", value="\n".join(free_lines), inline=False)
            if premium_lines:
                embed.add_field(name="💎 Premium Commands", value="\n".join(premium_lines), inline=False)
            await interaction.response.edit_message(embed=embed, view=self)
            return

        # remove suffix
        category_name = chosen.rsplit(" ", 1)[0]
        # category names in the mapping are original ones (without suffix)
        # find matching key
        matched = None
        for key in self.categories.keys():
            if key == category_name or (f"{key} (FREE)" in chosen) or (f"{key} (PREMIUM)" in chosen):
                matched = key
                break
        if not matched:
            # fallback: try to strip the appended "(FREE)/(PREMIUM)"
            matched = category_name

        items = self.categories.get(matched, [])
        embed = discord.Embed(title=f"{matched} — Commands", color=discord.Color.blurple())
        for it in items:
            name = it["cmd"]
            desc = it["desc"]
            if it.get("premium", False):
                name = f"💎 {name}"
            embed.add_field(name=name, value=desc, inline=False)

        embed.set_footer(text=f"{config.BOT_NAME} • {matched}")
        await interaction.response.edit_message(embed=embed, view=self)


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # canonical categories: each item is a dict with cmd, desc, premium(bool)
    HELP_CATEGORIES = {
        "🎵 Music Playback": [
            {"cmd": ".p / .play <song>", "desc": "Play a song (primary: .p).", "premium": False},
            {"cmd": ".join / /join", "desc": "Make the bot join your voice channel.", "premium": False},
            {"cmd": ".skip / /skip", "desc": "Skip the current track.", "premium": False},
            {"cmd": ".nowplaying / .np", "desc": "Show currently playing track.", "premium": False},
            {"cmd": ".stop / /stop", "desc": "Stop playback and leave the voice channel.", "premium": False},
        ],
        "📜 Queue & Navigation": [
            {"cmd": ".queue", "desc": "Show upcoming queue (next ~15).", "premium": False},
            {"cmd": ".skipto <position>", "desc": "Skip to a specific queue position (premium).", "premium": True},
            {"cmd": ".shuffle", "desc": "Shuffle the current queue (premium).", "premium": True},
            {"cmd": ".loop <off|track|queue>", "desc": "Set loop: 'track' is free, 'queue' is premium.", "premium": True},
        ],
        "❤️ Liked Songs": [
            {"cmd": ".like", "desc": "Like the currently playing song.", "premium": False},
            {"cmd": ".liked", "desc": "View your liked songs.", "premium": False},
            {"cmd": ".liked_clear", "desc": "Clear all your liked songs.", "premium": False},
        ],
        "💎 Premium": [
            {"cmd": ".grant_premium <guild_id>", "desc": "Owner-only: grant premium to a guild (paid).", "premium": True},
            {"cmd": ".revoke_premium <guild_id>", "desc": "Owner-only: revoke premium from a guild.", "premium": True},
            {"cmd": ".check_premium <guild_id>", "desc": "Owner-only: check premium status.", "premium": True},
            {"cmd": ".grant_premium_here", "desc": "Owner-only: grant premium to current guild.", "premium": True},
        ],
        "⚙ Utility": [
            {"cmd": ".help", "desc": "Show this interactive help menu.", "premium": False},
            {"cmd": ".lyrics <query>", "desc": "Get lyrics for a song (requires GENIUS_TOKEN).", "premium": False},
            {"cmd": ".pl-create <name>", "desc": "Create a personal playlist.", "premium": False},
            {"cmd": ".pl-add <playlist> <url>", "desc": "Add a track to a playlist.", "premium": False},
        ],
    }

    @commands.hybrid_command(name="help", description="Show the interactive help menu")
    async def help(self, ctx: commands.Context):
        """
        Hybrid help command.
        - If invoked as slash: send ephemeral reply.
        - If invoked as prefix: send visible reply in channel.
        """
        # Defer only for slash (so UI doesn't time out)
        if ctx.interaction:
            await ctx.interaction.response.defer(ephemeral=True)
            ephemeral = True
        else:
            ephemeral = False

        embed = discord.Embed(title=f"{config.BOT_NAME} — Help", color=discord.Color.blurple())
        embed.description = "Use the dropdown below to choose a category. Premium commands are marked with a 💎 badge."
        # Show a short overview: category list with counts and premium marker
        overview_lines = []
        for cat, items in self.HELP_CATEGORIES.items():
            has_premium = any(it.get("premium", False) for it in items)
            overview_lines.append(f"**{cat}** — {len(items)} commands {'• 💎 Premium' if has_premium else ''}")
        embed.add_field(name="Available Categories", value="\n".join(overview_lines), inline=False)
        embed.set_footer(text=f"{config.BOT_NAME} • Use the menu to view commands")

        view = HelpView(self.HELP_CATEGORIES, ephemeral=ephemeral)

        if ephemeral:
            # interaction was deferred earlier
            await ctx.interaction.followup.send(embed=embed, view=view, ephemeral=True)
        else:
            await ctx.reply(embed=embed, view=view, mention_author=False)


async def setup(bot):
    await bot.add_cog(Help(bot))
