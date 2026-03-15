from __future__ import annotations

import discord
from discord.ext import commands

from zero_config import CONFIG
from db import init_db
from premium_store import (
    grant_server_premium,
    has_active_vote_premium,
    is_guild_premium,
)


class PremiumCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db_init_task = bot.loop.create_task(init_db())

    async def get_conn(self):
        return await self.db_init_task

    @commands.hybrid_group(name="premium", invoke_without_command=True)
    async def premium_group(self, ctx: commands.Context) -> None:
        await self.status(ctx)

    @premium_group.command(name="status")
    async def status(self, ctx: commands.Context) -> None:
        conn = await self.get_conn()
        guild_premium = await is_guild_premium(conn, ctx.guild.id)
        vote_premium = await has_active_vote_premium(conn, ctx.author.id)

        embed = discord.Embed(
            title=f"Premium status for {ctx.guild.name}",
            colour=discord.Colour.blurple(),
        )
        embed.add_field(
            name="Server premium",
            value="✅ Active" if guild_premium else "❌ Inactive",
            inline=False,
        )
        embed.add_field(
            name="Your vote premium",
            value="✅ Active (12h window)" if vote_premium else "❌ Inactive",
            inline=False,
        )
        embed.set_footer(
            text="Vote on top.gg for 12 hours of premium access."
        )
        await ctx.reply(embed=embed, mention_author=False)

    @premium_group.command(name="grant")
    @commands.is_owner()
    async def grant(self, ctx: commands.Context) -> None:
        conn = await self.get_conn()
        await grant_server_premium(conn, ctx.guild.id, ctx.author.id)
        await ctx.reply(
            "✅ Permanent premium granted to this server.",
            mention_author=False,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(PremiumCog(bot))

