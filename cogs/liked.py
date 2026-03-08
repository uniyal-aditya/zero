# cogs/liked.py
import discord
from discord.ext import commands


class Liked(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _get_player(self, guild: discord.Guild):
        """Get the GuildPlayer from the MusicYT cog."""
        cog = self.bot.get_cog("MusicYT")
        if cog is None:
            return None
        return cog.players.get(guild.id)

    @commands.command(name="like")
    async def like(self, ctx: commands.Context):
        player = self._get_player(ctx.guild)
        if not player or not player.current:
            return await ctx.reply("Nothing is playing.", mention_author=False)
        tr = player.current
        # Track has: title, url, requester — store url as uri, empty author/length
        await self.bot.db.add_liked(
            ctx.author.id,
            track_uri=tr.url,
            title=tr.title,
            author=str(tr.requester),
            length=0,
        )
        await ctx.reply(f"❤️ Added **{tr.title}** to liked songs.", mention_author=False)

    @commands.command(name="liked")
    async def liked(self, ctx: commands.Context):
        rows = await self.bot.db.get_liked(ctx.author.id, limit=50)
        if not rows:
            return await ctx.reply("You have no liked songs.", mention_author=False)
        # row: (id, track_uri, title, author, length, added_at)
        lines = [f"`{i}.` **{r[2]}** — {r[3]}" for i, r in enumerate(rows, 1)]
        embed = discord.Embed(title="❤️ Your Liked Songs", description="\n".join(lines), color=discord.Color.red())
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot):
    await bot.add_cog(Liked(bot))
