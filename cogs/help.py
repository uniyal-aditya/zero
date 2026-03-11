# cogs/help.py
import discord
from discord.ext import commands
import config

CATEGORIES = {
    "🎵 Music": [
        (f"`{config.PREFIX}play / {config.PREFIX}p <query>`",    "Play a song by name or YouTube URL"),
        (f"`{config.PREFIX}search <query>`",                      "Search YouTube and pick a result"),
        (f"`{config.PREFIX}skip / {config.PREFIX}s`",            "Skip the current track"),
        (f"`{config.PREFIX}stop / {config.PREFIX}leave`",        "Stop music and disconnect"),
        (f"`{config.PREFIX}pause`",                               "Pause playback"),
        (f"`{config.PREFIX}resume / {config.PREFIX}r`",          "Resume playback"),
        (f"`{config.PREFIX}nowplaying / {config.PREFIX}np`",     "Show current track"),
        (f"`{config.PREFIX}queue / {config.PREFIX}q [page]`",    "View the queue"),
        (f"`{config.PREFIX}remove <pos>`",                       "Remove a track from queue"),
        (f"`{config.PREFIX}move <from> <to>`",                   "Move a track in the queue"),
        (f"`{config.PREFIX}clear`",                              "Clear the entire queue"),
        (f"`{config.PREFIX}loop [off/track/queue]`",             "Set loop mode"),
        (f"`{config.PREFIX}volume <0-200>`",                     "Set the volume"),
    ],
    "⭐ Premium Music": [
        (f"`{config.PREFIX}shuffle`",                            "Shuffle the queue"),
        (f"`{config.PREFIX}skipto <pos>`",                       "Jump to a queue position"),
        (f"`{config.PREFIX}filter <name>`",                      "Apply audio filters (bassboost, nightcore...)"),
        (f"`{config.PREFIX}247 on/off`",                         "Stay in VC 24/7"),
        ("`loop queue`",                                          "Queue loop mode"),
    ],
    "❤️ Liked Songs": [
        (f"`{config.PREFIX}like`",                               "Like the current song"),
        (f"`{config.PREFIX}liked`",                              "View your liked songs"),
        (f"`{config.PREFIX}likedplay`",                          "Queue all liked songs"),
        (f"`{config.PREFIX}unliked <pos>`",                      "Remove a liked song"),
    ],
    "📋 Playlists": [
        (f"`{config.PREFIX}pl create <n>`",                      "Create a playlist"),
        (f"`{config.PREFIX}pl add <n>`",                         "Add current song to playlist"),
        (f"`{config.PREFIX}pl play <n>`",                        "Queue an entire playlist"),
        (f"`{config.PREFIX}pl show <n>`",                        "View playlist tracks"),
        (f"`{config.PREFIX}pl list`",                            "List your playlists"),
        (f"`{config.PREFIX}pl delete <n>`",                      "Delete a playlist"),
    ],
    "🎤 Lyrics": [
        (f"`{config.PREFIX}lyrics [query]`",                     "Get lyrics for current/searched song"),
    ],
    "🔧 Utility": [
        (f"`{config.PREFIX}ping`",                               "Check bot latency"),
        (f"`{config.PREFIX}uptime`",                             "How long the bot has been running"),
        (f"`{config.PREFIX}invite`",                             "Get the invite link"),
        (f"`{config.PREFIX}guide`",                              "How to use Zero"),
        (f"`{config.PREFIX}premium`",                            "Premium info & status"),
        (f"`{config.PREFIX}claim`",                              "Claim 24h premium after voting on top.gg"),
        (f"`{config.PREFIX}votestatus`",                         "Check your vote/premium status"),
        (f"`{config.PREFIX}botinfo`",                            "Info about Zero"),
        (f"`{config.PREFIX}help`",                               "This help menu"),
    ],
}

class HelpSelect(discord.ui.Select):
    def __init__(self):
        opts = [discord.SelectOption(label=cat, description=f"{len(cmds)} commands") for cat, cmds in CATEGORIES.items()]
        super().__init__(placeholder="📂 Choose a category...", options=opts, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        cat = self.values[0]
        cmds = CATEGORIES[cat]
        embed = discord.Embed(title=f"{cat} Commands", color=0x5865F2)
        for name, desc in cmds:
            embed.add_field(name=name, value=desc, inline=False)
        embed.set_footer(text=f"Zero Music Bot | Prefix: {config.PREFIX}")
        await interaction.response.edit_message(embed=embed)

class HelpView(discord.ui.View):
    def __init__(self, author_id: int):
        super().__init__(timeout=120)
        self.author_id = author_id
        self.add_item(HelpSelect())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This menu isn't for you.", ephemeral=True)
            return False
        return True

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help", aliases=["h", "commands", "cmds"])
    async def help(self, ctx: commands.Context):
        """Show the help menu."""
        embed = discord.Embed(
            title=f"🎵 {config.BOT_NAME} — Help",
            description=(
                f"**Prefix:** `{config.PREFIX}` — also supports `/` slash commands\n\n"
                "Select a category below to see commands.\n\n"
                "**Quick Start:**\n"
                f"`{config.PREFIX}play <song>` — play music\n"
                f"`{config.PREFIX}search <query>` — search & pick\n"
                f"`{config.PREFIX}guide` — full guide\n"
            ),
            color=0x5865F2
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text=f"Made with ❤️ | {len(CATEGORIES)} categories")
        view = HelpView(ctx.author.id)
        await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Help(bot))
