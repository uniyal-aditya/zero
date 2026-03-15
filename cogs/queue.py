import discord
from discord.ext import commands
from discord import app_commands
import wavelink
from utils.embeds import err, ok, queue_embed


def get_player(ctx) -> wavelink.Player | None:
    return ctx.guild.voice_client


class Queue(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── QUEUE ─────────────────────────────────────────────────────────────────

    @commands.command(name="queue", aliases=["q"])
    async def queue(self, ctx: commands.Context, page: int = 1):
        """Show the music queue."""
        player = get_player(ctx)
        if not player or (not player.current and player.queue.is_empty):
            return await ctx.reply(embed=err("The queue is empty!"), mention_author=False)
        await ctx.reply(embed=queue_embed(player, page), mention_author=False)

    @app_commands.command(name="queue", description="📋 Show the music queue")
    @app_commands.describe(page="Page number")
    async def queue_slash(self, interaction: discord.Interaction, page: int = 1):
        ctx = await commands.Context.from_interaction(interaction)
        await self.queue(ctx, page)

    # ── SHUFFLE ───────────────────────────────────────────────────────────────

    @commands.command(name="shuffle")
    async def shuffle(self, ctx: commands.Context):
        """Shuffle the queue."""
        player = get_player(ctx)
        if not player or len(player.queue) < 2:
            return await ctx.reply(embed=err("Need at least 2 songs in the queue to shuffle."), mention_author=False)
        player.queue.shuffle()
        await ctx.reply(embed=ok(f"🔀 Shuffled **{len(player.queue)}** songs."), mention_author=False)

    @app_commands.command(name="shuffle", description="🔀 Shuffle the queue")
    async def shuffle_slash(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        await self.shuffle(ctx)

    # ── LOOP ──────────────────────────────────────────────────────────────────

    @commands.command(name="loop")
    async def loop(self, ctx: commands.Context):
        """Cycle loop mode: Off → Track → Queue → Off."""
        player = get_player(ctx)
        if not player:
            return await ctx.reply(embed=err("I'm not in a voice channel."), mention_author=False)
        modes = [wavelink.QueueMode.normal, wavelink.QueueMode.loop, wavelink.QueueMode.loop_all]
        labels = ["🔁 Loop **off**.", "🔂 Looping **current track**.", "🔁 Looping **entire queue**."]
        idx = modes.index(player.queue.mode) if player.queue.mode in modes else 0
        next_idx = (idx + 1) % len(modes)
        player.queue.mode = modes[next_idx]
        await ctx.reply(embed=ok(labels[next_idx]), mention_author=False)

    @app_commands.command(name="loop", description="🔁 Cycle loop mode")
    async def loop_slash(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        await self.loop(ctx)

    # ── AUTOPLAY ──────────────────────────────────────────────────────────────

    @commands.command(name="autoplay", aliases=["ap"])
    async def autoplay(self, ctx: commands.Context):
        """Toggle autoplay (adds related songs when queue ends)."""
        player = get_player(ctx)
        if not player:
            return await ctx.reply(embed=err("I'm not in a voice channel."), mention_author=False)
        player.autoplay_on = not getattr(player, "autoplay_on", False)
        msg = "🎵 Autoplay **enabled** — I'll keep the music going!" if player.autoplay_on else "🎵 Autoplay **disabled**."
        await ctx.reply(embed=ok(msg), mention_author=False)

    @app_commands.command(name="autoplay", description="♾️ Toggle autoplay")
    async def autoplay_slash(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        await self.autoplay(ctx)

    # ── SKIP TO ───────────────────────────────────────────────────────────────

    @commands.command(name="skipto", aliases=["st", "jump"])
    async def skipto(self, ctx: commands.Context, position: int = None):
        """Skip to a position in the queue."""
        player = get_player(ctx)
        if not player:
            return await ctx.reply(embed=err("I'm not in a voice channel."), mention_author=False)
        if position is None or position < 1 or position > len(player.queue):
            return await ctx.reply(embed=err(f"Invalid position. Queue has **{len(player.queue)}** songs."), mention_author=False)
        # Remove everything before that position
        for _ in range(position - 1):
            try:
                player.queue.get()
            except Exception:
                break
        await player.skip()
        await ctx.reply(embed=ok(f"⏭ Skipped to position **{position}**."), mention_author=False)

    @app_commands.command(name="skipto", description="⏭ Skip to a queue position")
    @app_commands.describe(position="Position in queue")
    async def skipto_slash(self, interaction: discord.Interaction, position: int):
        ctx = await commands.Context.from_interaction(interaction)
        await self.skipto(ctx, position)

    # ── REMOVE ────────────────────────────────────────────────────────────────

    @commands.command(name="remove", aliases=["rm"])
    async def remove(self, ctx: commands.Context, position: int = None):
        """Remove a track from the queue."""
        player = get_player(ctx)
        if not player:
            return await ctx.reply(embed=err("I'm not in a voice channel."), mention_author=False)
        tracks = list(player.queue)
        if position is None or position < 1 or position > len(tracks):
            return await ctx.reply(embed=err(f"Invalid position. Queue has **{len(tracks)}** songs."), mention_author=False)
        track = tracks[position - 1]
        player.queue.remove(track)
        await ctx.reply(embed=ok(f"🗑 Removed **{track.title}**."), mention_author=False)

    @app_commands.command(name="remove", description="🗑 Remove a song from the queue")
    @app_commands.describe(position="Position in queue")
    async def remove_slash(self, interaction: discord.Interaction, position: int):
        ctx = await commands.Context.from_interaction(interaction)
        await self.remove(ctx, position)

    # ── MOVE ──────────────────────────────────────────────────────────────────

    @commands.command(name="move")
    async def move(self, ctx: commands.Context, from_pos: int = None, to_pos: int = None):
        """Move a track to a different position."""
        player = get_player(ctx)
        if not player:
            return await ctx.reply(embed=err("I'm not in a voice channel."), mention_author=False)
        tracks = list(player.queue)
        if any(p is None or p < 1 or p > len(tracks) for p in [from_pos, to_pos]):
            return await ctx.reply(embed=err(f"Invalid positions. Queue has **{len(tracks)}** songs."), mention_author=False)
        track = tracks.pop(from_pos - 1)
        tracks.insert(to_pos - 1, track)
        player.queue.clear()
        for t in tracks:
            player.queue.put(t)
        await ctx.reply(embed=ok(f"↕️ Moved **{track.title}** to position **{to_pos}**."), mention_author=False)

    @app_commands.command(name="move", description="↕️ Move a song in the queue")
    @app_commands.describe(from_pos="Current position", to_pos="New position")
    async def move_slash(self, interaction: discord.Interaction, from_pos: int, to_pos: int):
        ctx = await commands.Context.from_interaction(interaction)
        await self.move(ctx, from_pos, to_pos)

    # ── CLEAR ─────────────────────────────────────────────────────────────────

    @commands.command(name="clear")
    async def clear(self, ctx: commands.Context):
        """Clear the queue (keeps current song playing)."""
        player = get_player(ctx)
        if not player:
            return await ctx.reply(embed=err("I'm not in a voice channel."), mention_author=False)
        count = len(player.queue)
        player.queue.clear()
        await ctx.reply(embed=ok(f"🧹 Cleared **{count}** songs from the queue."), mention_author=False)

    @app_commands.command(name="clear", description="🧹 Clear the queue")
    async def clear_slash(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        await self.clear(ctx)


async def setup(bot):
    await bot.add_cog(Queue(bot))
