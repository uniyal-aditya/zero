# cogs/playlist.py
import discord
from discord.ext import commands
from core.ytdl import fetch_track
from core.player import Track

class Playlist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_player(self, guild):
        cog = self.bot.get_cog("Music")
        return cog.get_player(guild) if cog else None

    @commands.group(name="pl", aliases=["playlist"], invoke_without_command=True)
    async def pl(self, ctx: commands.Context):
        """Playlist commands. Use `.pl help` for subcommands."""
        embed = discord.Embed(title="📋 Playlist Commands", color=0x5865F2, description=(
            "`.pl create <name>` — Create a playlist\n"
            "`.pl delete <name>` — Delete a playlist\n"
            "`.pl add <name>` — Add current song to playlist\n"
            "`.pl play <name>` — Play a playlist\n"
            "`.pl show <name>` — Show playlist tracks\n"
            "`.pl list` — List your playlists"
        ))
        await ctx.send(embed=embed)

    @pl.command(name="create")
    async def pl_create(self, ctx: commands.Context, *, name: str):
        ok = await self.bot.db.pl_create(ctx.author.id, name)
        if ok:
            await ctx.send(f"✅ Playlist **{name}** created.")
        else:
            await ctx.send(f"❌ A playlist named **{name}** already exists.")

    @pl.command(name="delete", aliases=["del", "remove"])
    async def pl_delete(self, ctx: commands.Context, *, name: str):
        ok = await self.bot.db.pl_delete(ctx.author.id, name)
        await ctx.send(f"✅ Deleted **{name}**." if ok else f"❌ Playlist **{name}** not found.")

    @pl.command(name="add")
    async def pl_add(self, ctx: commands.Context, *, name: str):
        player = self.get_player(ctx.guild)
        if not player or not player.current:
            return await ctx.send("❌ Nothing is playing.")
        ok = await self.bot.db.pl_add_track(
            ctx.author.id, name,
            player.current.title, player.current.webpage_url
        )
        if ok:
            await ctx.send(f"✅ Added **{player.current.title}** to `{name}`.")
        else:
            await ctx.send(f"❌ Playlist **{name}** not found. Create it first with `.pl create {name}`.")

    @pl.command(name="play")
    async def pl_play(self, ctx: commands.Context, *, name: str):
        if not ctx.author.voice:
            return await ctx.send("❌ Join a voice channel first.")
        tracks = await self.bot.db.pl_tracks(ctx.author.id, name)
        if not tracks:
            return await ctx.send(f"❌ Playlist **{name}** not found or empty.")
        player = self.get_player(ctx.guild)
        if not player:
            return await ctx.send("❌ Music system unavailable.")
        await player.connect(ctx.author.voice.channel)
        msg = await ctx.send(f"⏳ Loading **{len(tracks)}** tracks from `{name}`...")
        loaded = 0
        for title, url in tracks:
            data = await fetch_track(url)
            if data and data["url"]:
                player.add_to_queue(Track(
                    title=data["title"], url=data["url"],
                    webpage_url=data["webpage_url"], duration=data["duration"],
                    requester=ctx.author, thumbnail=data["thumbnail"]
                ))
                loaded += 1
        await player.start()
        await msg.edit(content=f"✅ Queued **{loaded}** tracks from playlist `{name}`.")

    @pl.command(name="show", aliases=["view", "tracks"])
    async def pl_show(self, ctx: commands.Context, *, name: str):
        tracks = await self.bot.db.pl_tracks(ctx.author.id, name)
        if not tracks:
            return await ctx.send(f"❌ Playlist **{name}** not found or empty.")
        lines = "\n".join(f"`{i}.` {t[0]}" for i, t in enumerate(tracks, 1))
        embed = discord.Embed(title=f"📋 {name}", description=lines[:4000], color=0x5865F2)
        embed.set_footer(text=f"{len(tracks)} tracks")
        await ctx.send(embed=embed)

    @pl.command(name="list", aliases=["all"])
    async def pl_list(self, ctx: commands.Context):
        pls = await self.bot.db.pl_list(ctx.author.id)
        if not pls:
            return await ctx.send("📭 You have no playlists. Create one with `.pl create <name>`.")
        lines = "\n".join(f"`{i}.` **{name}** — {cnt} tracks" for i, (name, cnt) in enumerate(pls, 1))
        embed = discord.Embed(title="📋 Your Playlists", description=lines, color=0x5865F2)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Playlist(bot))
