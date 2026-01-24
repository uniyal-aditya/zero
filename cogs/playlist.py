# cogs/playlist.py
from discord.ext import commands

class Playlist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db

    @commands.command(name="pl-create")
    async def pl_create(self, ctx: commands.Context, *, name: str):
        await self.db.create_playlist(ctx.author.id, name)
        await ctx.send(f"Created playlist `{name}`.")

    @commands.command(name="pl-add")
    async def pl_add(self, ctx: commands.Context, playlist: str, *, url: str):
        # Basic: uses title=url for now
        ok = await self.db.add_track_to_playlist(ctx.author.id, playlist, url, url)
        if ok:
            await ctx.send(f"Added track to `{playlist}`.")
        else:
            await ctx.send("Playlist not found.")

    @commands.command(name="pl-play")
    async def pl_play(self, ctx: commands.Context, playlist: str):
        rows = await self.db.get_playlist_tracks(ctx.author.id, playlist)
        if not rows:
            return await ctx.send("Playlist not found or empty.")
        # For simplicity, push to queue sequentially
        vc = ctx.guild.voice_client
        if not vc:
            await ctx.author.voice.channel.connect(cls=self.bot.get_cog("Music").__class__.player)
        for title, url in rows:
            await vc.queue.put(url)
        await ctx.send(f"Queued {len(rows)} tracks from `{playlist}`.")

async def setup(bot):
    await bot.add_cog(Playlist(bot))
