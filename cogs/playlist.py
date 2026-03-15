import discord
from discord.ext import commands
from discord import app_commands
import wavelink
import utils.database as db
from utils.embeds import err, ok, _ms_to_str
import config as cfg


def player(ctx) -> wavelink.Player | None:
    return ctx.guild.voice_client if ctx.guild else None


class Playlist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="pl", aliases=["playlist"], invoke_without_command=True)
    async def pl(self, ctx: commands.Context):
        await ctx.send(embed=err("Usage: `-pl <create|delete|list|view|add|remove|play|rename>`"))

    @pl.command(name="create")
    async def pl_create(self, ctx: commands.Context, *, name: str):
        if len(name) > 32:
            return await ctx.send(embed=err("Name must be ≤ 32 characters."))
        if len(db.get_playlists(ctx.author.id)) >= 25:
            return await ctx.send(embed=err("You can have at most **25** playlists."))
        if not db.create_playlist(ctx.author.id, name):
            return await ctx.send(embed=err(f"A playlist named **{name}** already exists."))
        await ctx.send(embed=ok(f"📁 Created playlist **{name}**."))

    @pl.command(name="delete", aliases=["del"])
    async def pl_delete(self, ctx: commands.Context, *, name: str):
        if not db.delete_playlist(ctx.author.id, name):
            return await ctx.send(embed=err(f"No playlist named **{name}** found."))
        await ctx.send(embed=ok(f"🗑 Deleted **{name}**."))

    @pl.command(name="list")
    async def pl_list(self, ctx: commands.Context):
        playlists = db.get_playlists(ctx.author.id)
        if not playlists:
            return await ctx.send(embed=err("You have no playlists. Create one with `-pl create <name>`."))
        entries = list(playlists.values())
        e = discord.Embed(
            title=f"📁  {ctx.author.display_name}'s Playlists",
            description="\n".join(f"**{i+1}.** {p['name']} — {len(p['songs'])} songs" for i, p in enumerate(entries)),
            colour=cfg.COL_PRIMARY,
        )
        e.set_footer(text=f"{len(entries)}/25 playlists • Made by Aditya</>")
        await ctx.send(embed=e)

    @pl.command(name="view", aliases=["show"])
    async def pl_view(self, ctx: commands.Context, *, name: str):
        pl = db.get_playlist(ctx.author.id, name)
        if not pl:
            return await ctx.send(embed=err(f"No playlist named **{name}** found."))
        songs = pl["songs"][:20]
        desc = "\n".join(f"`{i+1}.` [{s['title']}]({s['url']}) — `{s['duration']}`" for i, s in enumerate(songs)) \
               or "No songs yet. Use `-pl add <name>` while a song plays."
        e = discord.Embed(title=f"📁  {pl['name']}", description=desc, colour=cfg.COL_PRIMARY)
        e.set_footer(text=f"{len(pl['songs'])} songs{' (showing first 20)' if len(pl['songs'])>20 else ''} • Made by Aditya</>")
        await ctx.send(embed=e)

    @pl.command(name="add", aliases=["save"])
    async def pl_add(self, ctx: commands.Context, *, name: str):
        vc = player(ctx)
        if not vc or not vc.current:
            return await ctx.send(embed=err("Nothing is playing right now."))
        t = vc.current
        song = {"title": t.title, "url": t.uri, "duration": _ms_to_str(t.length), "author": t.author}
        if not db.add_song_to_playlist(ctx.author.id, name, song):
            return await ctx.send(embed=err(f"No playlist named **{name}** found."))
        await ctx.send(embed=ok(f"✅ Added **{t.title}** to **{name}**."))

    @pl.command(name="remove", aliases=["rm"])
    async def pl_remove(self, ctx: commands.Context, name: str, position: int):
        if not db.remove_song_from_playlist(ctx.author.id, name, position - 1):
            return await ctx.send(embed=err("Invalid playlist name or position."))
        await ctx.send(embed=ok(f"🗑 Removed song #{position} from **{name}**."))

    @pl.command(name="play", aliases=["start"])
    async def pl_play(self, ctx: commands.Context, *, name: str):
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send(embed=err("You must be in a voice channel!"))
        pl = db.get_playlist(ctx.author.id, name)
        if not pl:
            return await ctx.send(embed=err(f"No playlist named **{name}** found."))
        if not pl["songs"]:
            return await ctx.send(embed=err(f"**{name}** is empty."))
        vc: wavelink.Player = ctx.guild.voice_client
        if not vc:
            vc = await ctx.author.voice.channel.connect(cls=wavelink.Player, self_deaf=True)
            vc.home = ctx.channel
            vc.autoplay_on = False
        await ctx.send(embed=ok(f"▶️ Loading **{pl['name']}** ({len(pl['songs'])} songs)…"))
        loaded = 0
        for song in pl["songs"]:
            try:
                results = await wavelink.Playable.search(song["url"])
                if results:
                    await vc.queue.put_wait(results[0])
                    loaded += 1
            except Exception:
                pass
        if not vc.playing and not vc.queue.is_empty:
            await vc.play(vc.queue.get())
        await ctx.channel.send(embed=ok(f"✅ Loaded **{loaded}/{len(pl['songs'])}** songs from **{pl['name']}**."))

    @pl.command(name="rename")
    async def pl_rename(self, ctx: commands.Context, old: str, *, new: str):
        result = db.rename_playlist(ctx.author.id, old, new)
        if result is False:
            return await ctx.send(embed=err(f"No playlist named **{old}** found."))
        if result == "exists":
            return await ctx.send(embed=err(f"**{new}** already exists."))
        await ctx.send(embed=ok(f"✏️ Renamed **{old}** → **{new}**."))


async def setup(bot):
    await bot.add_cog(Playlist(bot))
