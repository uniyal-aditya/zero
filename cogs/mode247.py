# cogs/mode247.py
from discord.ext import commands

class Mode247(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db

    @commands.command(name="247")
    async def mode247(self, ctx: commands.Context, arg: str = None):
        # require premium check for demonstration
        is_premium = await self.db.is_premium_user(ctx.author.id)
        if not is_premium:
            return await ctx.send("This feature is premium-only.")
        if arg is None:
            status = await self.db.is_247(ctx.guild.id)
            return await ctx.send(f"24/7 is {'enabled' if status else 'disabled'}.")
        if arg.lower() in ("on", "enable", "1", "true"):
            await self.db.set_247(ctx.guild.id, True)
            return await ctx.send("24/7 enabled.")
        elif arg.lower() in ("off", "disable", "0", "false"):
            await self.db.set_247(ctx.guild.id, False)
            return await ctx.send("24/7 disabled.")
        else:
            return await ctx.send("Usage: .247 on/off")

async def setup(bot):
    await bot.add_cog(Mode247(bot))
