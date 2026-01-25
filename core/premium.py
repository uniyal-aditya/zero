# cogs/premium.py
import discord
from discord.ext import commands

class PremiumAdmin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="premium_add")
    @commands.is_owner()
    async def premium_add(self, ctx: commands.Context, guild_id: int):
        """Grant premium to a guild (owner-only)."""
        try:
            await self.bot.db.add_premium_guild(guild_id, activated_by=ctx.author.id)
            await ctx.send(f"✅ Premium granted to guild `{guild_id}`.")
        except Exception as e:
            await ctx.send(f"❌ DB error: {e}")

    @commands.command(name="premium_remove")
    @commands.is_owner()
    async def premium_remove(self, ctx: commands.Context, guild_id: int):
        """Revoke premium (owner-only)."""
        try:
            await self.bot.db.remove_premium_guild(guild_id)
            await ctx.send(f"✅ Premium revoked for guild `{guild_id}`.")
        except Exception as e:
            await ctx.send(f"❌ DB error: {e}")

    @commands.command(name="premium_list")
    @commands.is_owner()
    async def premium_list(self, ctx: commands.Context):
        try:
            lst = await self.bot.db.list_premium_guilds()
            if not lst:
                return await ctx.send("No premium guilds.")
            await ctx.send("Premium guilds:\n" + "\n".join(str(g) for g in lst))
        except Exception as e:
            await ctx.send(f"❌ DB error: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(PremiumAdmin(bot))
