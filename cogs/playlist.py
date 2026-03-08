# cogs/playlist.py
import discord
from discord.ext import commands


class Playlist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db

    def _get_player(self, guild: discord.Guild):
        cog = self.bot.get_cog("MusicYT")
        if cog is None:
            return None
        return cog.get_player(guild)

    @commands.command(name="pl-create")
    async def pl_create(self, ctx: commands.Context, *, name: str):
        await self.db.create_playlist(ctx.author.id, name)
        await ctx.send(f"✅ Created playlist `{name}`.")

    @commands.command(name="pl-add")
    async def pl_add(self, ctx: commands.Context, playlist: str, *, url: str):
        # Use title=url as a fallback label
        ok = await self.db.add_track(ctx.author.id, playlist, url, url)
        if ok:
            await ctx.send(f"✅ Added track to `{playlist}`.")
        else:
            await ctx.send(f"❌ Playlist `{playlist}` not found. Create it first with `.pl-create`.")

    @commands.command(name="pl-play")
    async def pl_play(self, ctx: commands.Context, playlist: str):
        rows = await self.db.get_playlist(ctx.author.id, playlist)
        if not rows:
            return await ctx.send(f"❌ Playlist `{playlist}` not found or empty.")

        if not ctx.author.voice:
            return await ctx.send("Join a voice channel first.")

        music_cog = self.bot.get_cog("MusicYT")
        if music_cog is None:
            return await ctx.send("❌ Music system unavailable.")

        player = music_cog.get_player(ctx.guild)
        await player.connect(ctx.author.voice.channel)

        from cogs.music_yt import Track
        queued = 0
        for title, url in rows:
            data = await music_cog.yt_search(url)
            if data and data[0]:
                resolved_url, resolved_title = data
                await player.add(Track(resolved_title or title, resolved_url, ctx.author))
                queued += 1

        await ctx.send(f"📋 Queued **{queued}** tracks from `{playlist}`.")

    @commands.command(name="pl-list")
    async def pl_list(self, ctx: commands.Context):
        rows = await self.db.list_playlists(ctx.author.id)
        if not rows:
            return await ctx.send("You have no playlists. Create one with `.pl-create <name>`.")
        lines = [f"`{i}.` {name} ({count} tracks)" for i, (name, count) in enumerate(rows, 1)]
        await ctx.send("📋 Your playlists:\n" + "\n".join(lines))


async def setup(bot):
    await bot.add_cog(Playlist(bot))
