import discord
from discord.ext import commands
from discord import app_commands
import wavelink
from utils.embeds import err, ok, queue_embed


def player(ctx) -> wavelink.Player | None:
    return ctx.guild.voice_client if ctx.guild else None


class Queue(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="queue", aliases=["q"], description="📋 Show the music queue")
    @app_commands.describe(page="Page number")
    async def queue(self, ctx: commands.Context, page: int = 1):
        vc = player(ctx)
        if not vc or (not vc.current and vc.queue.is_empty):
            return await ctx.send(embed=err("The queue is empty!"))
        await ctx.send(embed=queue_embed(vc, page))

    @commands.hybrid_command(name="shuffle", description="🔀 Shuffle the queue")
    async def shuffle(self, ctx: commands.Context):
        vc = player(ctx)
        if not vc or len(vc.queue) < 2:
            return await ctx.send(embed=err("Need at least 2 songs in the queue to shuffle."))
        vc.queue.shuffle()
        await ctx.send(embed=ok(f"🔀 Shuffled **{len(vc.queue)}** songs."))

    @commands.hybrid_command(name="loop", description="🔁 Cycle loop mode: Off → Track → Queue")
    async def loop(self, ctx: commands.Context):
        vc = player(ctx)
        if not vc:
            return await ctx.send(embed=err("I'm not in a voice channel."))
        modes  = [wavelink.QueueMode.normal, wavelink.QueueMode.loop, wavelink.QueueMode.loop_all]
        labels = ["🔁 Loop **off**.", "🔂 Looping **current track**.", "🔁 Looping **entire queue**."]
        idx    = modes.index(vc.queue.mode) if vc.queue.mode in modes else 0
        nxt    = (idx + 1) % len(modes)
        vc.queue.mode = modes[nxt]
        await ctx.send(embed=ok(labels[nxt]))

    @commands.hybrid_command(name="autoplay", aliases=["ap"], description="♾️ Toggle autoplay")
    async def autoplay(self, ctx: commands.Context):
        vc = player(ctx)
        if not vc:
            return await ctx.send(embed=err("I'm not in a voice channel."))
        vc.autoplay_on = not getattr(vc, "autoplay_on", False)
        msg = "🎵 Autoplay **enabled** — I'll keep the music going!" if vc.autoplay_on else "🎵 Autoplay **disabled**."
        await ctx.send(embed=ok(msg))

    @commands.hybrid_command(name="skipto", aliases=["jump"], description="⏭ Skip to a position in the queue")
    @app_commands.describe(position="Position to skip to")
    async def skipto(self, ctx: commands.Context, position: int):
        vc = player(ctx)
        if not vc:
            return await ctx.send(embed=err("I'm not in a voice channel."))
        if position < 1 or position > len(vc.queue):
            return await ctx.send(embed=err(f"Invalid position. Queue has **{len(vc.queue)}** songs."))
        for _ in range(position - 1):
            try:
                vc.queue.get()
            except Exception:
                break
        await vc.skip()
        await ctx.send(embed=ok(f"⏭ Skipped to position **{position}**."))

    @commands.hybrid_command(name="remove", aliases=["rm"], description="🗑 Remove a track from the queue")
    @app_commands.describe(position="Position to remove")
    async def remove(self, ctx: commands.Context, position: int):
        vc = player(ctx)
        if not vc:
            return await ctx.send(embed=err("I'm not in a voice channel."))
        tracks = list(vc.queue)
        if position < 1 or position > len(tracks):
            return await ctx.send(embed=err(f"Invalid position. Queue has **{len(tracks)}** songs."))
        track = tracks[position - 1]
        vc.queue.remove(track)
        await ctx.send(embed=ok(f"🗑 Removed **{track.title}**."))

    @commands.hybrid_command(name="move", description="↕️ Move a track to a different position")
    @app_commands.describe(from_pos="Current position", to_pos="New position")
    async def move(self, ctx: commands.Context, from_pos: int, to_pos: int):
        vc = player(ctx)
        if not vc:
            return await ctx.send(embed=err("I'm not in a voice channel."))
        tracks = list(vc.queue)
        if any(p < 1 or p > len(tracks) for p in [from_pos, to_pos]):
            return await ctx.send(embed=err(f"Invalid positions. Queue has **{len(tracks)}** songs."))
        track = tracks.pop(from_pos - 1)
        tracks.insert(to_pos - 1, track)
        vc.queue.clear()
        for t in tracks:
            vc.queue.put(t)
        await ctx.send(embed=ok(f"↕️ Moved **{track.title}** to position **{to_pos}**."))

    @commands.hybrid_command(name="clear", description="🧹 Clear the queue (keeps current song)")
    async def clear(self, ctx: commands.Context):
        vc = player(ctx)
        if not vc:
            return await ctx.send(embed=err("I'm not in a voice channel."))
        count = len(vc.queue)
        vc.queue.clear()
        await ctx.send(embed=ok(f"🧹 Cleared **{count}** songs from the queue."))


async def setup(bot):
    await bot.add_cog(Queue(bot))
