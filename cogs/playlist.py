from discord.ext import commands
import wavelink

class Playlist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def playlist(self, ctx, action, name=None):
        if action == "create":
            await self.bot.db.create_playlist(ctx.author.id, name)
            return await ctx.send(f"📁 Playlist `{name}` created.")

        if action == "add":
            vc = ctx.guild.voice_client
            if not vc or not vc.current_track:
                return await ctx.send("Nothing playing.")
            ok = await self.bot.db.add_track(
                ctx.author.id, name,
                vc.current_track.title,
                vc.current_track.uri
            )
            return await ctx.send("✅ Added to playlist." if ok else "Playlist not found.")

        if action == "play":
            tracks = await self.bot.db.get_playlist(ctx.author.id, name)
            if not tracks:
                return await ctx.send("Playlist empty or not found.")
            vc = ctx.guild.voice_client
            for title, url in tracks:
                track = await wavelink.YouTubeTrack.search(url, return_first=True)
                await vc.queue.put(track)
            if not vc.playing:
                await vc.play(await vc.queue.get())
            await ctx.send(f"▶ Playing playlist `{name}`.")

async def setup(bot):
    await bot.add_cog(Playlist(bot))
