from __future__ import annotations

import asyncio

import discord
from discord.ext import commands

from zero_config import CONFIG
from topgg_server import run_topgg_server_in_background


class ZeroBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.voice_states = True

        super().__init__(
            command_prefix=commands.when_mentioned_or(CONFIG.prefix),
            intents=intents,
            case_insensitive=True,
        )

    async def setup_hook(self) -> None:
        await self.load_extension("music_player")
        await self.load_extension("premium_cog")
        await self.load_extension("help_cog")

        run_topgg_server_in_background(self.loop)

        await self.tree.sync()
        print("✅ Slash commands synced.")

    async def on_ready(self) -> None:
        print(f"✅ Logged in as {self.user} (ID: {self.user.id})")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name="/play | -help",
            )
        )

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        # If the bot is directly mentioned without extra text, show the about/help embed
        if (
            message.guild
            and len(message.mentions) == 1
            and message.mentions[0].id == self.user.id
            and message.content.strip() in {self.user.mention, f"<@!{self.user.id}>"}
        ):
            owner_mention = f"<@{CONFIG.owner_id}>"
            embed = discord.Embed(
                title="Zero – High Definition Music Bot",
                description=(
                    "Zero brings **premium, high‑definition music** to your server with playlists, "
                    "likes, 24/7 mode, and powerful queue controls.\n\n"
                    "Use `/play` or `-play` to start listening, and `/premium` to see premium status."
                ),
                colour=discord.Colour.blurple(),
            )
            embed.add_field(
                name="Key features",
                value=(
                    "• HD music from YouTube & Spotify links\n"
                    "• `/play` / `/p` and `-play` / `-p`\n"
                    "• Shuffle, loop, autoplay, back, forward, pause, resume\n"
                    "• Playlists, liked songs, 24/7 voice support\n"
                    "• Premium access via top.gg votes or server unlock"
                ),
                inline=False,
            )
            embed.add_field(
                name="Getting started",
                value=(
                    "• `/play <song or link>` – start playing music\n"
                    "• `/queue`, `/nowplaying` – manage the current session\n"
                    "• `/premium` – view your premium perks\n"
                    f"• Prefix commands: `-play`, `-skip`, `-loop`, `-queue`, `-premium`"
                ),
                inline=False,
            )
            embed.set_footer(text="made by Aditya</>")

            await message.channel.send(
                content=f"Hey {owner_mention}, someone pinged your bot!",
                embed=embed,
                allowed_mentions=discord.AllowedMentions(users=True),
            )

        await self.process_commands(message)


async def main() -> None:
    if not CONFIG.discord_token:
        raise RuntimeError("DISCORD_TOKEN not set in environment.")

    bot = ZeroBot()
    async with bot:
        await bot.start(CONFIG.discord_token)


if __name__ == "__main__":
    asyncio.run(main())

