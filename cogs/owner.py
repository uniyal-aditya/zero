import discord
from discord.ext import commands
import config as cfg
from utils.embeds import err, ok


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, ctx):
        if ctx.author.id != cfg.OWNER_ID:
            raise commands.CheckFailure("This command is restricted to the bot owner.")
        return True

    @commands.command(name="eval")
    async def eval_cmd(self, ctx: commands.Context, *, code: str):
        import traceback, io, contextlib
        output = io.StringIO()
        env = {"bot": self.bot, "ctx": ctx, "discord": discord}
        try:
            exec(f"async def __e():\n" + "\n".join(f"    {l}" for l in code.split("\n")), env)
            with contextlib.redirect_stdout(output):
                await env["__e"]()
            result = output.getvalue() or "✅ No output."
        except Exception:
            result = traceback.format_exc()
        e = discord.Embed(title="Eval", description=f"```py\n{result[:1900]}\n```", colour=cfg.COL_PRIMARY)
        await ctx.send(embed=e)

    @commands.command(name="setstatus")
    async def setstatus(self, ctx: commands.Context, *, text: str):
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=text))
        await ctx.send(embed=ok(f"✅ Status set to: **{text}**"))

    @commands.command(name="announce")
    async def announce(self, ctx: commands.Context, *, text: str):
        await ctx.send(embed=ok(f"📢 Sending to {len(self.bot.guilds)} servers…"))
        sent = failed = 0
        for guild in self.bot.guilds:
            try:
                owner = await guild.fetch_member(guild.owner_id)
                await owner.send(f"📢 **Zero Music Announcement**\n\n{text}")
                sent += 1
            except Exception:
                failed += 1
        await ctx.channel.send(embed=ok(f"Sent: **{sent}** ✅   Failed: **{failed}** ❌"))

    @commands.command(name="servers")
    async def servers(self, ctx: commands.Context):
        guilds = sorted(self.bot.guilds, key=lambda g: g.member_count or 0, reverse=True)
        lines  = [f"`{i+1}.` **{g.name}** — {g.member_count} members (`{g.id}`)" for i,g in enumerate(guilds[:20])]
        e = discord.Embed(title=f"🌐  Zero is in {len(guilds)} servers",
                          description="\n".join(lines) or "None.", colour=cfg.COL_PRIMARY)
        e.set_footer(text="Made by Aditya</>")
        await ctx.send(embed=e)


async def setup(bot):
    await bot.add_cog(Owner(bot))
