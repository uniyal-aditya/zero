# cogs/help.py
import discord
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    FREE = [
        "p / play", "skip", "queue", "pause", "resume", "nowplaying"
    ]
    PREMIUM = [
        "loop", "shuffle", "skipto", "24/7"
    ]

    @commands.hybrid_command(name="help")
    async def help(self, ctx):
        embed = discord.Embed(title="Zero™ Help Menu", color=0x5865F2)
        embed.add_field(
            name="🎵 Free Commands",
            value="\n".join(f"`{c}`" for c in self.FREE),
            inline=False,
        )
        embed.add_field(
            name="💎 Premium Commands",
            value="\n".join(f"`{c}`" for c in self.PREMIUM),
            inline=False,
        )
        embed.set_footer(text="Premium unlocks for the whole server.")
        await ctx.reply(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))
