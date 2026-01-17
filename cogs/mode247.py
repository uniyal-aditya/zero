from discord.ext import commands

class Mode247(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="247")
    async def toggle_247(self, ctx, mode: str):
        if not await self.bot.db.is_premium_user(ctx.author.id):
            return await ctx.send("💎 Premium required for 24/7 mode.")

        enable = mode.lower() == "on"
        await self.bot.db.set_247(ctx.guild.id, enable)
        await ctx.send(f"🔒 24/7 mode {'enabled' if enable else 'disabled'}.")

async def setup(bot):
    await bot.add_cog(Mode247(bot))
