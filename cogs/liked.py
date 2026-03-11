# cogs/liked.py
import discord
from discord.ext import commands
from core.player import Track
from core.ytdl import fetch_track

class Liked(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_player(self, guild):
        cog = self.bot.get_cog("Music")
        return cog.get_player(guild) if cog else None

    @commands.command(name="like", aliases=["❤️"])
    async def like(self, ctx: commands.Context):
        """Like the current song."""
        player = self.get_player(ctx.guild)
        if not player or not player.current:
            return await ctx.send("❌ Nothing is playing.")
        t = player.current
        await self.bot.db.add_liked(ctx.author.id, t.webpage_url, t.title)
        await ctx.send(f"❤️ Added **{t.title}** to your liked songs.")

    @commands.command(name="liked", aliases=["favorites", "fav"])
    async def liked(self, ctx: commands.Context):
        """View your liked songs."""
        rows = await self.bot.db.get_liked(ctx.author.id)
        if not rows:
            return await ctx.send("💔 You have no liked songs yet. Use `.like` while a song is playing.")
        lines = "\n".join(f"`{i}.` {r[2]}" for i, r in enumerate(rows, 1))
        embed = discord.Embed(title=f"❤️ {ctx.author.display_name}'s Liked Songs",
                              description=lines[:4000], color=0xe74c3c)
        embed.set_footer(text=f"{len(rows)} songs")
        await ctx.send(embed=embed)

    @commands.command(name="likedplay", aliases=["playliked", "favplay"])
    async def likedplay(self, ctx: commands.Context):
        """Queue all your liked songs."""
        if not ctx.author.voice:
            return await ctx.send("❌ Join a voice channel first.")
        rows = await self.bot.db.get_liked(ctx.author.id)
        if not rows:
            return await ctx.send("💔 You have no liked songs.")
        player = self.get_player(ctx.guild)
        await player.connect(ctx.author.voice.channel)
        msg = await ctx.send(f"⏳ Loading **{len(rows)}** liked songs...")
        loaded = 0
        for _, url, title in rows:
            data = await fetch_track(url)
            if data and data["url"]:
                player.add_to_queue(Track(
                    title=data["title"], url=data["url"],
                    webpage_url=data["webpage_url"], duration=data["duration"],
                    requester=ctx.author, thumbnail=data["thumbnail"]
                ))
                loaded += 1
        await player.start()
        await msg.edit(content=f"✅ Queued **{loaded}** liked songs.")

    @commands.command(name="unliked", aliases=["unlike"])
    async def unliked(self, ctx: commands.Context, pos: int):
        """Remove a song from liked by position."""
        rows = await self.bot.db.get_liked(ctx.author.id)
        if not rows or not (1 <= pos <= len(rows)):
            return await ctx.send("❌ Invalid position.")
        liked_id, _, title = rows[pos - 1]
        await self.bot.db.remove_liked(ctx.author.id, liked_id)
        await ctx.send(f"💔 Removed **{title}** from liked songs.")


async def setup(bot):
    await bot.add_cog(Liked(bot))
