# cogs/premium.py
import discord
from discord.ext import commands

OWNER_ID = YOUR_DISCORD_ID_HERE  # change this

class Premium(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="premium_add")
    async def premium_add(self, ctx, guild_id: int):
        if ctx.author.id != OWNER_ID:
            return
        await self.bot.db.add_premium_guild(guild_id)
        await ctx.send("✅ Premium added.")

    @commands.command(name="premium_remove")
    async def premium_remove(self, ctx, guild_id: int):
        if ctx.author.id != OWNER_ID:
            return
        await self.bot.db.remove_premium_guild(guild_id)
        await ctx.send("❌ Premium removed.")

async def setup(bot):
    await bot.add_cog(Premium(bot))
