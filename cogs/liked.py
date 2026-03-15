import discord
from discord.ext import commands
from discord import app_commands
import wavelink
import utils.database as db
from utils.embeds import err, ok
import config as cfg


def get_player(ctx) -> wavelink.Player | None:
    return ctx.guild.voice_client


class Liked(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="like")
    async def like(self, ctx: commands.Context):
        """Like the currently playing song."""
        player = get_player(ctx)
        if not player or not player.current:
            return await ctx.reply(embed=err("Nothing is playing!"), mention_author=False)
        t = player.current
        from utils.embeds import _ms_to_str
        song = {"title": t.title, "url": t.uri, "duration": _ms_to_str(t.length), "author": t.author}
        if not db.like_song(ctx.author.id, song):
            return await ctx.reply(embed=err("This song is already in your liked songs!"), mention_author=False)
        await ctx.reply(embed=ok(f"❤️ Added **{t.title}** to your liked songs."), mention_author=False)

    @app_commands.command(name="like", description="❤️ Like the currently playing song")
    async def like_slash(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        await self.like(ctx)

    @commands.command(name="unlike")
    async def unlike(self, ctx: commands.Context):
        """Unlike the currently playing song."""
        player = get_player(ctx)
        if not player or not player.current:
            return await ctx.reply(embed=err("Nothing is playing!"), mention_author=False)
        if not db.unlike_song(ctx.author.id, player.current.uri):
            return await ctx.reply(embed=err("This song is not in your liked songs."), mention_author=False)
        await ctx.reply(embed=ok(f"💔 Removed **{player.current.title}** from liked songs."), mention_author=False)

    @app_commands.command(name="unlike", description="💔 Unlike the currently playing song")
    async def unlike_slash(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        await self.unlike(ctx)

    @commands.command(name="liked", aliases=["favorites", "fav"])
    async def liked(self, ctx: commands.Context, action: str = None):
        """View or play your liked songs. Use `-liked play` to queue all."""
        songs = db.get_liked_songs(ctx.author.id)

        if action and action.lower() in ("play", "start"):
            if not ctx.author.voice or not ctx.author.voice.channel:
                return await ctx.reply(embed=err("You must be in a voice channel!"), mention_author=False)
            if not songs:
                return await ctx.reply(embed=err("Your liked songs list is empty!"), mention_author=False)
            player: wavelink.Player = ctx.guild.voice_client
            if not player:
                player = await ctx.author.voice.channel.connect(cls=wavelink.Player, self_deaf=True)
                player.home = ctx.channel
                player.autoplay_on = False
            await ctx.reply(embed=ok(f"▶️ Loading **{len(songs)}** liked songs…"), mention_author=False)
            loaded = 0
            for song in songs:
                try:
                    results = await wavelink.Playable.search(song["url"])
                    if results:
                        await player.queue.put_wait(results[0])
                        loaded += 1
                except Exception:
                    pass
            if not player.playing and not player.queue.is_empty:
                await player.play(player.queue.get())
            return await ctx.channel.send(embed=ok(f"✅ Queued **{loaded}** liked songs."))

        # View
        desc = "\n".join(
            f"`{i+1}.` [{s['title']}]({s['url']}) — `{s['duration']}`"
            for i, s in enumerate(songs[:20])
        ) or "No liked songs yet!\nUse `-like` while a song plays to add it here."
        e = discord.Embed(
            title=f"❤️  {ctx.author.display_name}'s Liked Songs",
            description=desc,
            colour=cfg.COL_ERROR,
        )
        e.set_footer(text=f"{len(songs)} songs • `-liked play` to queue all • Made by Aditya</>")
        await ctx.reply(embed=e, mention_author=False)

    @app_commands.command(name="liked", description="❤️ View or play your liked songs")
    @app_commands.describe(action="Use 'play' to queue all liked songs")
    async def liked_slash(self, interaction: discord.Interaction, action: str = None):
        ctx = await commands.Context.from_interaction(interaction)
        await self.liked(ctx, action)


async def setup(bot):
    await bot.add_cog(Liked(bot))
