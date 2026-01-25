# cogs/liked.py
import discord
from discord.ext import commands

class Liked(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="like")
    async def like(self, ctx: commands.Context):
        vc = ctx.guild.voice_client
        if not vc or not getattr(vc, "current_track", None):
            return await ctx.reply("Nothing is playing.", mention_author=False)
        tr = vc.current_track
        await self.bot.db.add_liked(ctx.author.id, getattr(tr, "uri", ""), tr.title, getattr(tr, "author", ""), getattr(tr, "length", 0))
        await ctx.reply("Added to liked songs.", mention_author=False)

    @commands.command(name="liked")
    async def liked(self, ctx: commands.Context):
        rows = await self.bot.db.get_liked(ctx.author.id, limit=50)
        if not rows:
            return await ctx.reply("You have no liked songs.", mention_author=False)
        lines = [f"`{r[0]}` {r[2]} — {r[3]}" for r in rows]
        await ctx.reply("Your liked songs:\n" + "\n".join(lines), mention_author=False)

async def setup(bot):
    await bot.add_cog(Liked(bot))
