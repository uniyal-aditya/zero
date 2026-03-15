import discord
from discord.ext import commands
import config as cfg
from utils.embeds import err, ok


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, ctx: commands.Context) -> bool:
        if ctx.author.id != cfg.OWNER_ID:
            raise commands.CheckFailure("This command is restricted to the bot owner.")
        return True

    # ── EVAL ──────────────────────────────────────────────────────────────────

    @commands.command(name="eval")
    async def eval_cmd(self, ctx: commands.Context, *, code: str = None):
        """Run Python code (owner only)."""
        if not code:
            return await ctx.reply(embed=err("Provide code to evaluate."), mention_author=False)
        import traceback, io, contextlib
        output = io.StringIO()
        try:
            with contextlib.redirect_stdout(output):
                exec(
                    f"async def __eval():\n" +
                    "\n".join(f"    {line}" for line in code.split("\n")),
                    {"bot": self.bot, "ctx": ctx, "discord": discord}
                )
                import asyncio
                result = await eval("__eval()", {"bot": self.bot, "ctx": ctx, "discord": discord, "__eval": locals()["__eval"]})
        except Exception:
            result = traceback.format_exc()
        out = output.getvalue() or str(result) or "No output."
        e = discord.Embed(
            title="✅ Eval Result",
            description=f"```py\n{out[:1900]}\n```",
            colour=cfg.COL_PRIMARY,
        )
        await ctx.reply(embed=e, mention_author=False)

    # ── SET STATUS ────────────────────────────────────────────────────────────

    @commands.command(name="setstatus")
    async def setstatus(self, ctx: commands.Context, *, text: str = None):
        """Set the bot's playing status (owner only)."""
        if not text:
            return await ctx.reply(embed=err("Provide status text."), mention_author=False)
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=text))
        await ctx.reply(embed=ok(f"✅ Status set to: **{text}**"), mention_author=False)

    # ── ANNOUNCE ──────────────────────────────────────────────────────────────

    @commands.command(name="announce")
    async def announce(self, ctx: commands.Context, *, text: str = None):
        """DM all guild owners (owner only)."""
        if not text:
            return await ctx.reply(embed=err("Provide an announcement message."), mention_author=False)
        await ctx.reply(embed=ok(f"📢 Sending to {len(self.bot.guilds)} servers…"), mention_author=False)
        sent = failed = 0
        for guild in self.bot.guilds:
            try:
                owner = await guild.fetch_member(guild.owner_id)
                await owner.send(f"📢 **Zero Music Announcement**\n\n{text}")
                sent += 1
            except Exception:
                failed += 1
        await ctx.channel.send(embed=ok(f"Sent: **{sent}** ✅   Failed: **{failed}** ❌"))

    # ── SERVERS ───────────────────────────────────────────────────────────────

    @commands.command(name="servers")
    async def servers(self, ctx: commands.Context):
        """List all servers the bot is in (owner only)."""
        guilds = sorted(self.bot.guilds, key=lambda g: g.member_count, reverse=True)
        lines  = [f"`{i+1}.` **{g.name}** — {g.member_count} members (`{g.id}`)" for i, g in enumerate(guilds[:20])]
        e = discord.Embed(
            title=f"🌐  Zero is in {len(guilds)} servers",
            description="\n".join(lines) or "None.",
            colour=cfg.COL_PRIMARY,
        )
        e.set_footer(text="Made by Aditya</>")
        await ctx.reply(embed=e, mention_author=False)


async def setup(bot):
    await bot.add_cog(Owner(bot))
