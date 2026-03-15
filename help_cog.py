from __future__ import annotations

import discord
from discord.ext import commands

from zero_config import CONFIG


class HelpView(discord.ui.View):
    def __init__(self, *, timeout: float | None = 60.0) -> None:
        super().__init__(timeout=timeout)
        self.add_item(HelpSelect())


class HelpSelect(discord.ui.Select):
    def __init__(self) -> None:
        options = [
            discord.SelectOption(
                label="Overview",
                description="What Zero is and how to start.",
                value="overview",
                emoji="🎧",
            ),
            discord.SelectOption(
                label="Music commands",
                description="Play, queue, shuffle, loop, 24/7, etc.",
                value="music",
                emoji="🎵",
            ),
            discord.SelectOption(
                label="Premium & voting",
                description="How premium works and top.gg.",
                value="premium",
                emoji="💎",
            ),
            discord.SelectOption(
                label="Playlists & likes",
                description="(Planned) manage playlists and favorites.",
                value="playlists",
                emoji="📂",
            ),
        ]
        super().__init__(
            placeholder="Select a category to view help…",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        value = self.values[0]
        owner_mention = f"<@{CONFIG.owner_id}>"

        if value == "overview":
            embed = discord.Embed(
                title="Zero – Help Overview",
                description=(
                    "Zero is a **high‑definition music bot** with playlists, likes, 24/7 mode, "
                    "and vote‑based premium.\n\n"
                    f"Use slash commands like `/play` or prefix commands like `{CONFIG.prefix}play`.\n"
                    "Select another category below to see detailed commands."
                ),
                colour=discord.Colour.blurple(),
            )
            embed.add_field(
                name="Quick start",
                value=(
                    "1. Join a voice channel.\n"
                    "2. Run `/play <song or link>` or "
                    f"`{CONFIG.prefix}play <song or link>`.\n"
                    "3. Use `/queue`, `/skip`, `/loop` to control playback."
                ),
                inline=False,
            )
        elif value == "music":
            embed = discord.Embed(
                title="Music commands",
                colour=discord.Colour.blurple(),
            )
            embed.add_field(
                name="Play & control",
                value=(
                    f"`/play`, `/p`, `{CONFIG.prefix}play`, `{CONFIG.prefix}p` – play from YouTube/Spotify links or search\n"
                    f"`/skip`, `{CONFIG.prefix}skip` – skip current track\n"
                    f"`/pause`, `/resume`, `{CONFIG.prefix}pause`, `{CONFIG.prefix}resume` – control playback\n"
                    f"`/stop`, `{CONFIG.prefix}stop` – stop and clear queue"
                ),
                inline=False,
            )
            embed.add_field(
                name="Queue & loop",
                value=(
                    f"`/queue`, `{CONFIG.prefix}queue` – view queue\n"
                    f"`/nowplaying`, `{CONFIG.prefix}nowplaying` – what is playing\n"
                    f"`/shuffle`, `{CONFIG.prefix}shuffle` – shuffle queue\n"
                    f"`/loop <off|track|queue|autoplay>`, `{CONFIG.prefix}loop` – set loop/autoplay mode"
                ),
                inline=False,
            )
        elif value == "premium":
            embed = discord.Embed(
                title="Premium & top.gg voting",
                colour=discord.Colour.blurple(),
            )
            embed.add_field(
                name="Server premium",
                value=(
                    "Zero supports **per‑server premium** which can be unlocked only by the bot owner.\n"
                    "Server premium enables all premium‑only music and playlist features for everyone in that server."
                ),
                inline=False,
            )
            embed.add_field(
                name="Vote‑based premium (12 hours)",
                value=(
                    "When you **vote for Zero on top.gg**, you get **12 hours of premium access**.\n"
                    "This is automatically detected via the vote webhook.\n"
                    "Use `/premium` or "
                    f"`{CONFIG.prefix}premium` to see your status."
                ),
                inline=False,
            )
        else:  # playlists
            embed = discord.Embed(
                title="Playlists & liked songs",
                colour=discord.Colour.blurple(),
            )
            embed.description = (
                "Zero stores playlist and liked‑song data so you can build custom queues.\n"
                "Playlist and like commands are planned; once enabled you will be able to:\n\n"
                "• Create personal or server playlists\n"
                "• Add the currently playing track to a playlist\n"
                "• Like songs and play from your liked tracks"
            )

        embed.set_footer(text="made by Aditya</>")
        await interaction.response.edit_message(embed=embed, view=self.view)


class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="help", description="Show Zero's organised help menu.")
    async def help_cmd(self, ctx: commands.Context) -> None:
        owner_mention = f"<@{CONFIG.owner_id}>"
        embed = discord.Embed(
            title="Zero – Help Menu",
            description=(
                "Welcome to **Zero**, your high‑definition music bot.\n\n"
                "Use the selector below to browse help categories, or start with **Overview**.\n"
                f"Bot owner: {owner_mention}"
            ),
            colour=discord.Colour.blurple(),
        )
        embed.set_footer(text="made by Aditya</>")

        view = HelpView(timeout=120.0)
        await ctx.reply(embed=embed, view=view, mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HelpCog(bot))

