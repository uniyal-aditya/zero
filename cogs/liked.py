# cogs/liked.py
import discord
from discord.ext import commands
from discord import app_commands
import json
from core.db import Database
import asyncio

class Liked(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # db instance attached to bot in bot.py
        self.db: Database = bot.db

    def _track_info(self, track):
        return {
            "uri": getattr(track, "uri", None),
            "title": getattr(track, "title", "Unknown"),
            "author": getattr(track, "author", "Unknown"),
            "length": getattr(track, "length", 0)
        }

    # Prefix .like
    @commands.command(name="like")
    async def like_prefix(self, ctx: commands.Context):
        vc = ctx.guild.voice_client
        if not vc or not vc.current_track:
            return await ctx.send("Nothing is playing to like.")
        track = vc.current_track
        info = self._track_info(track)
        await self.db.add_liked(ctx.author.id, info["uri"], info["title"], info["author"], info["length"])
        await ctx.send(f"❤️ Added **{info['title']}** to your liked songs.")

    @app_commands.command(name="like", description="Like the current playing song")
    async def like_slash(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        vc = interaction.guild.voice_client
        if not vc or not vc.current_track:
            return await interaction.followup.send("Nothing is playing.", ephemeral=True)
        track = vc.current_track
        info = self._track_info(track)
        await self.db.add_liked(interaction.user.id, info["uri"], info["title"], info["author"], info["length"])
        await interaction.followup.send(f"❤️ Liked **{info['title']}**", ephemeral=True)

    @commands.command(name="liked")
    async def liked_prefix(self, ctx: commands.Context, action: str = None, index: int = None):
        # .liked (shows), .liked play, .liked play 3, .liked shuffle, .liked remove 3
        uid = ctx.author.id
        rows = await self.db.get_liked(uid, limit=200)
        if not rows:
            return await ctx.send("You have no liked songs.")
        if not action:
            # show top 12
            lines = []
            for r in rows[:12]:
                lines.append(f"`{r[0]}` {r[2]} - {r[3]}")
            return await ctx.send("**Your liked songs:**\n" + "\n".join(lines))
        action = action.lower()
        if action in ("play", "playall"):
            # enqueue all liked
            vc = ctx.guild.voice_client
            if not vc:
                # connect
                if not ctx.author.voice or not ctx.author.voice.channel:
                    return await ctx.send("Join a voice channel first.")
                await ctx.author.voice.channel.connect(cls=self.bot.get_cog("Music").__class__.__bases__[0])
                vc = ctx.guild.voice_client
            for r in rows:
                # use uri or fallback to title search
                if r[1]:
                    try:
                        t = await self.bot.loop.run_in_executor(None, lambda: None)  # placeholder
                    except Exception:
                        t = None
                # fallback: search YouTube by title
                tracks = await wavelink.YouTubeTrack.search(r[2], return_first=True)
                if tracks:
                    await vc.queue.put(tracks)
            if not vc.playing:
                nextt = await vc.queue.get()
                await vc.play(nextt)
            await ctx.send("▶️ Enqueued your liked songs.")
            return
        if action == "shuffle":
            import random
            list_rows = list(rows)
            random.shuffle(list_rows)
            # enqueue similar to above
            vc = ctx.guild.voice_client
            if not vc:
                if not ctx.author.voice or not ctx.author.voice.channel:
                    return await ctx.send("Join a voice channel first.")
                await ctx.author.voice.channel.connect(cls=self.bot.get_cog("Music").__class__.__bases__[0])
                vc = ctx.guild.voice_client
            for r in list_rows:
                tracks = await wavelink.YouTubeTrack.search(r[2], return_first=True)
                if tracks:
                    await vc.queue.put(tracks)
            if not vc.playing:
                nextt = await vc.queue.get()
                await vc.play(nextt)
            return await ctx.send("🔀 Shuffled and enqueued liked songs.")

        if action in ("remove", "unlike"):
            if index is None:
                return await ctx.send("Provide the liked id to remove (see `.liked` list).")
            await self.db.remove_liked(uid, index)
            return await ctx.send(f"🗑️ Removed liked id `{index}`.")
        if action == "clear":
            await self.db.clear_liked(uid)
            return await ctx.send("🧹 Cleared all liked songs.")
        if action == "count":
            c = await self.db.count_liked(uid)
            return await ctx.send(f"You have **{c}** liked songs.")
        if action == "recent":
            lines = []
            for r in rows[:10]:
                lines.append(f"`{r[0]}` {r[2]} - {r[3]}")
            return await ctx.send("**Recent liked:**\n" + "\n".join(lines))
        await ctx.send("Unknown subcommand for `.liked`.")

    @app_commands.command(name="liked", description="Manage your liked songs (play, shuffle, remove, clear, count)")
    async def liked_slash(self, interaction: discord.Interaction, sub: Optional[str] = None, index: Optional[int] = None):
        await interaction.response.defer()
        # keep slash simpler: /liked sub:play|shuffle|remove|clear|count|recent
        uid = interaction.user.id
        rows = await self.db.get_liked(uid, limit=200)
        if not rows:
            return await interaction.followup.send("You have no liked songs.", ephemeral=True)
        if not sub:
            # show top 8
            lines = []
            for r in rows[:8]:
                lines.append(f"`{r[0]}` {r[2]} - {r[3]}")
            return await interaction.followup.send("**Your liked songs:**\n" + "\n".join(lines), ephemeral=True)
        sub = sub.lower()
        if sub == "play":
            vc = interaction.guild.voice_client
            if not vc:
                if not interaction.user.voice or not interaction.user.voice.channel:
                    return await interaction.followup.send("Join a voice channel first.", ephemeral=True)
                await interaction.user.voice.channel.connect(cls=self.bot.get_cog("Music").__class__.__bases__[0])
                vc = interaction.guild.voice_client
            for r in rows:
                # search by title fallback
                t = await wavelink.YouTubeTrack.search(r[2], return_first=True)
                if t:
                    await vc.queue.put(t)
            if not vc.playing:
                nextt = await vc.queue.get()
                await vc.play(nextt)
            return await interaction.followup.send("▶️ Enqueued your liked songs.", ephemeral=True)
        if sub == "shuffle":
            import random
            random.shuffle(rows)
            vc = interaction.guild.voice_client
            if not vc:
                if not interaction.user.voice or not interaction.user.voice.channel:
                    return await interaction.followup.send("Join a voice channel first.", ephemeral=True)
                await interaction.user.voice.channel.connect(cls=self.bot.get_cog("Music").__class__.__bases__[0])
                vc = interaction.guild.voice_client
            for r in rows:
                t = await wavelink.YouTubeTrack.search(r[2], return_first=True)
                if t:
                    await vc.queue.put(t)
            if not vc.playing:
                nextt = await vc.queue.get()
                await vc.play(nextt)
            return await interaction.followup.send("🔀 Shuffled & enqueued liked songs.", ephemeral=True)
        if sub in ("remove", "unlike"):
            if not index:
                return await interaction.followup.send("Provide liked id to remove.", ephemeral=True)
            await self.db.remove_liked(uid, index)
            return await interaction.followup.send(f"🗑️ Removed liked id `{index}`.", ephemeral=True)
        if sub == "clear":
            await self.db.clear_liked(uid)
            return await interaction.followup.send("🧹 Cleared all liked songs.", ephemeral=True)
        if sub == "count":
            c = await self.db.count_liked(uid)
            return await interaction.followup.send(f"You have **{c}** liked songs.", ephemeral=True)
        if sub == "recent":
            lines = []
            for r in rows[:10]:
                lines.append(f"`{r[0]}` {r[2]} - {r[3]}")
            return await interaction.followup.send("**Recent liked:**\n" + "\n".join(lines), ephemeral=True)

    @commands.command(name="liked_export")
    async def liked_export_prefix(self, ctx: commands.Context):
        data = await self.db.export_liked(ctx.author.id)
        if not data:
            return await ctx.send("No liked songs to export.")
        payload = json.dumps(data, indent=2)
        await ctx.send(file=discord.File(fp=discord.File.__init__.__globals__['io'].BytesIO(payload.encode()), filename="liked_export.json"))

    @commands.command(name="liked_import")
    async def liked_import_prefix(self, ctx: commands.Context):
        if not ctx.message.attachments:
            return await ctx.send("Attach a JSON export to import.")
        attach = ctx.message.attachments[0]
        blob = await attach.read()
        try:
            items = json.loads(blob.decode())
        except Exception:
            return await ctx.send("Invalid JSON.")
        await self.db.import_liked(ctx.author.id, items)
        await ctx.send("✅ Imported liked songs.")

async def setup(bot):
    await bot.add_cog(Liked(bot))
