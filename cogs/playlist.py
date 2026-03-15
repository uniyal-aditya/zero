import discord
from discord.ext import commands
from discord import app_commands
import wavelink
import utils.database as db
from utils.embeds import err, ok
import config as cfg


def get_player(ctx) -> wavelink.Player | None:
    return ctx.guild.voice_client


class Playlist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="pl", aliases=["playlist"], invoke_without_command=True)
    async def pl(self, ctx: commands.Context):
        """Playlist management. Use `-pl help` or subcommands."""
        await ctx.reply(embed=err(
            "Usage: `-pl <create|delete|list|view|add|remove|play|rename>`\n"
            "Try `-help playlist` for details."
        ), mention_author=False)

    # ── CREATE ────────────────────────────────────────────────────────────────

    @pl.command(name="create")
    async def pl_create(self, ctx: commands.Context, *, name: str = None):
        if not name:
            return await ctx.reply(embed=err("Provide a playlist name."), mention_author=False)
        if len(name) > 32:
            return await ctx.reply(embed=err("Name must be ≤ 32 characters."), mention_author=False)
        if len(db.get_playlists(ctx.author.id)) >= 25:
            return await ctx.reply(embed=err("You can have at most **25** playlists."), mention_author=False)
        if not db.create_playlist(ctx.author.id, name):
            return await ctx.reply(embed=err(f"A playlist named **{name}** already exists."), mention_author=False)
        await ctx.reply(embed=ok(f"📁 Created playlist **{name}**."), mention_author=False)

    # ── DELETE ────────────────────────────────────────────────────────────────

    @pl.command(name="delete", aliases=["del"])
    async def pl_delete(self, ctx: commands.Context, *, name: str = None):
        if not name:
            return await ctx.reply(embed=err("Provide the playlist name."), mention_author=False)
        if not db.delete_playlist(ctx.author.id, name):
            return await ctx.reply(embed=err(f"No playlist named **{name}** found."), mention_author=False)
        await ctx.reply(embed=ok(f"🗑 Deleted **{name}**."), mention_author=False)

    # ── LIST ──────────────────────────────────────────────────────────────────

    @pl.command(name="list")
    async def pl_list(self, ctx: commands.Context):
        playlists = db.get_playlists(ctx.author.id)
        if not playlists:
            return await ctx.reply(embed=err("You have no playlists. Create one with `-pl create <n>`."), mention_author=False)
        entries = list(playlists.values())
        e = discord.Embed(
            title=f"📁  {ctx.author.display_name}'s Playlists",
            description="\n".join(f"**{i+1}.** {p['name']} — {len(p['songs'])} songs" for i, p in enumerate(entries)),
            colour=cfg.COL_PRIMARY,
        )
        e.set_footer(text=f"{len(entries)}/25 playlists • Made by Aditya</>")
        await ctx.reply(embed=e, mention_author=False)

    # ── VIEW ──────────────────────────────────────────────────────────────────

    @pl.command(name="view", aliases=["show"])
    async def pl_view(self, ctx: commands.Context, *, name: str = None):
        if not name:
            return await ctx.reply(embed=err("Provide the playlist name."), mention_author=False)
        pl = db.get_playlist(ctx.author.id, name)
        if not pl:
            return await ctx.reply(embed=err(f"No playlist named **{name}** found."), mention_author=False)
        songs = pl["songs"][:20]
        desc = "\n".join(f"`{i+1}.` [{s['title']}]({s['url']}) — `{s['duration']}`" for i, s in enumerate(songs)) \
               or "No songs yet. Use `-pl add <n>` while a song plays."
        e = discord.Embed(title=f"📁  {pl['name']}", description=desc, colour=cfg.COL_PRIMARY)
        e.set_footer(text=f"{len(pl['songs'])} songs{' (showing first 20)' if len(pl['songs']) > 20 else ''} • Made by Aditya</>")
        await ctx.reply(embed=e, mention_author=False)

    # ── ADD ───────────────────────────────────────────────────────────────────

    @pl.command(name="add", aliases=["save"])
    async def pl_add(self, ctx: commands.Context, *, name: str = None):
        if not name:
            return await ctx.reply(embed=err("Provide the playlist name."), mention_author=False)
        player = get_player(ctx)
        if not player or not player.current:
            return await ctx.reply(embed=err("Nothing is playing right now."), mention_author=False)
        t = player.current
        from utils.embeds import _ms_to_str
        song = {"title": t.title, "url": t.uri, "duration": _ms_to_str(t.length), "author": t.author}
        if not db.add_song_to_playlist(ctx.author.id, name, song):
            return await ctx.reply(embed=err(f"No playlist named **{name}** found."), mention_author=False)
        await ctx.reply(embed=ok(f"✅ Added **{t.title}** to **{name}**."), mention_author=False)

    # ── REMOVE ────────────────────────────────────────────────────────────────

    @pl.command(name="remove", aliases=["rm"])
    async def pl_remove(self, ctx: commands.Context, name: str = None, position: int = None):
        if not name or position is None:
            return await ctx.reply(embed=err("Usage: `-pl remove <playlist> <position>`"), mention_author=False)
        if not db.remove_song_from_playlist(ctx.author.id, name, position - 1):
            return await ctx.reply(embed=err("Invalid playlist name or position."), mention_author=False)
        await ctx.reply(embed=ok(f"🗑 Removed song #{position} from **{name}**."), mention_author=False)

    # ── PLAY ──────────────────────────────────────────────────────────────────

    @pl.command(name="play", aliases=["start"])
    async def pl_play(self, ctx: commands.Context, *, name: str = None):
        if not name:
            return await ctx.reply(embed=err("Provide the playlist name."), mention_author=False)
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.reply(embed=err("You must be in a voice channel!"), mention_author=False)
        pl = db.get_playlist(ctx.author.id, name)
        if not pl:
            return await ctx.reply(embed=err(f"No playlist named **{name}** found."), mention_author=False)
        if not pl["songs"]:
            return await ctx.reply(embed=err(f"**{name}** is empty."), mention_author=False)

        player: wavelink.Player = ctx.guild.voice_client
        if not player:
            player = await ctx.author.voice.channel.connect(cls=wavelink.Player, self_deaf=True)
            player.home = ctx.channel
            player.autoplay_on = False

        await ctx.reply(embed=ok(f"▶️ Loading **{pl['name']}** ({len(pl['songs'])} songs)…"), mention_author=False)
        loaded = 0
        for song in pl["songs"]:
            try:
                results = await wavelink.Playable.search(song["url"])
                if results:
                    t = results[0]
                    await player.queue.put_wait(t)
                    loaded += 1
            except Exception:
                pass
        if not player.playing and not player.queue.is_empty:
            await player.play(player.queue.get())
        await ctx.channel.send(embed=ok(f"✅ Loaded **{loaded}/{len(pl['songs'])}** songs from **{pl['name']}**."))

    # ── RENAME ────────────────────────────────────────────────────────────────

    @pl.command(name="rename")
    async def pl_rename(self, ctx: commands.Context, old: str = None, *, new: str = None):
        if not old or not new:
            return await ctx.reply(embed=err("Usage: `-pl rename <old> <new>`"), mention_author=False)
        result = db.rename_playlist(ctx.author.id, old, new)
        if result is False:
            return await ctx.reply(embed=err(f"No playlist named **{old}** found."), mention_author=False)
        if result == "exists":
            return await ctx.reply(embed=err(f"**{new}** already exists."), mention_author=False)
        await ctx.reply(embed=ok(f"✏️ Renamed **{old}** → **{new}**."), mention_author=False)


async def setup(bot):
    await bot.add_cog(Playlist(bot))
