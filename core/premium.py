# cogs/premium.py
import discord
from discord.ext import commands

class PremiumCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.is_owner()
    @commands.command(name="grant_premium")
    async def grant_premium(self, ctx: commands.Context, guild_id: int):
        await self.bot.db.grant_guild_premium(guild_id)
        await ctx.send(f"Granted premium to {guild_id}")

    @commands.is_owner()
    @commands.command(name="revoke_premium")
    async def revoke_premium(self, ctx: commands.Context, guild_id: int):
        await self.bot.db.revoke_guild_premium(guild_id)
        await ctx.send(f"Revoked premium from {guild_id}")

    @commands.command(name="check_premium")
    async def check_premium(self, ctx: commands.Context, guild_id: int = None):
        if guild_id is None:
            guild_id = ctx.guild.id
        ok = await self.bot.db.is_guild_premium(guild_id)
        await ctx.send(f"Guild {guild_id} premium: {ok}")

    @commands.command(name="buy_premium")
    async def buy_premium(self, ctx: commands.Context):
        # simple manual instructions: actual payment must POST to webhook /payment-webhook with PAYMENT_SECRET
        if ctx.author.id != ctx.guild.owner_id:
            return await ctx.send("Only the server owner may purchase premium for this server.")
        # give user instructions
        payment_url = f"Please use the owner dashboard/payments page to purchase. (Contact bot owner)"
        await ctx.send(payment_url)

async def setup(bot):
    await bot.add_cog(PremiumCog(bot))
