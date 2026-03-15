import discord
from discord.ext import commands
from discord import app_commands
import wavelink
import utils.database as db
from utils.embeds import err, ok, _ms_to_str
import config as cfg


def player(ctx) -> wavelink.Player | None:
    return ctx.guild.voice_client if ctx.guild else None


class Liked(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="like", description="❤️ Like the currently playing song")
    async def like(self, ctx: commands.Context):
        vc = player(ctx)
        if not vc or not vc.current:
            return await ctx.send(embed=err("Nothing is playing!"))
        t = vc.current
        song = {"title": t.title, "url": t.uri, "duration": _ms_to_str(t.length), "author": t.author}
        if not db.like_song(ctx.author.id, song):
            return await ctx.send(embed=err("Already in your liked songs!"))
        await ctx.send(embed=ok(f"❤️ Added **{t.title}** to your liked songs."))

    @commands.hybrid_command(name="unlike", description="💔 Unlike the currently playing song")
    async def unlike(self, ctx: commands.Context):
        vc = player(ctx)
        if not vc or not vc.current:
            return await ctx.send(embed=err("Nothing is playing!"))
        if not db.unlike_song(ctx.author.id, vc.current.uri):
            return await ctx.send(embed=err("This song is not in your liked songs."))
        await ctx.send(embed=ok(f"💔 Removed **{vc.current.title}** from liked songs."))

    @commands.hybrid_command(name="liked", aliases=["favorites", "fav"], description="❤️ View or play liked songs")
    @app_commands.describe(action="Use 'play' to queue all liked songs")
    async def liked(self, ctx: commands.Context, action: str = None):
        songs = db.get_liked_songs(ctx.author.id)
        if action and action.lower() in ("play", "start"):
            await ctx.defer()
            if not ctx.author.voice or not ctx.author.voice.channel:
                return await ctx.send(embed=err("You must be in a voice channel!"))
            if not songs:
                return await ctx.send(embed=err("Your liked songs list is empty!"))
            vc: wavelink.Player = ctx.guild.voice_client
            if not vc:
                vc = await ctx.author.voice.channel.connect(cls=wavelink.Player, self_deaf=True)
                vc.home = ctx.channel
                vc.autoplay_on = False
            await ctx.send(embed=ok(f"▶️ Loading **{len(songs)}** liked songs…"))
            loaded = 0
            for song in songs:
                try:
                    results = await wavelink.Playable.search(song["url"])
                    if results:
                        await vc.queue.put_wait(results[0])
                        loaded += 1
                except Exception:
                    pass
            if not vc.playing and not vc.queue.is_empty:
                await vc.play(vc.queue.get())
            return await ctx.channel.send(embed=ok(f"✅ Queued **{loaded}** liked songs."))

        desc = "\n".join(
            f"`{i+1}.` [{s['title']}]({s['url']}) — `{s['duration']}`"
            for i, s in enumerate(songs[:20])
        ) or "No liked songs yet!\nUse `-like` while a song plays."
        e = discord.Embed(
            title=f"❤️  {ctx.author.display_name}'s Liked Songs",
            description=desc,
            colour=cfg.COL_ERROR,
        )
        e.set_footer(text=f"{len(songs)} songs • `-liked play` to queue all • Made by Aditya</>")
        await ctx.send(embed=e)


async def setup(bot):
    await bot.add_cog(Liked(bot))
