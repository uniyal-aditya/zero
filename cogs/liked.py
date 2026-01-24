# cogs/liked.py
import discord
from discord.ext import commands
import config

class Liked(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db

    def _track_info(self, track):
        return {
            "uri": getattr(track, "uri", ""),
            "title": getattr(track, "title", "Unknown"),
            "author": getattr(track, "author", "Unknown"),
            "length": getattr(track, "length", 0)
        }

    @commands.command(name="like")
    async def like_prefix(self, ctx: commands.Context):
        vc = ctx.guild.voice_client
        if not vc or not getattr(vc, "current_track", None):
            return await ctx.send("Nothing is playing to like.")
        info = self._track_info(vc.current_track)
        await self.db.add_liked(ctx.author.id, info["uri"], info["title"], info["author"], info["length"])
        await ctx.send(f"❤️ Added **{info['title']}** to your liked songs.")

    @commands.command(name="liked")
    async def liked_prefix(self, ctx: commands.Context):
        rows = await self.db.get_liked(ctx.author.id, limit=25)
        if not rows:
            return await ctx.send("You have no liked songs.")
        lines = [f"`{r[0]}` {r[2]} — {r[3]}" for r in rows]
        await ctx.send("**Your liked songs:**\n" + "\n".join(lines))

    @commands.command(name="liked_clear")
    async def liked_clear(self, ctx: commands.Context):
        await self.db.clear_liked(ctx.author.id)
        await ctx.send("Cleared your liked songs.")

async def setup(bot):
    await bot.add_cog(Liked(bot))
