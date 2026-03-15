import discord
from discord.ext import commands
from discord import app_commands
import wavelink
import time
import utils.database as db
from utils.embeds import err, ok, premium_wall
from utils.topgg import has_voted
import config as cfg


def player(ctx) -> wavelink.Player | None:
    return ctx.guild.voice_client if ctx.guild else None


FILTERS = {
    "bass":       wavelink.Filters(equalizer=wavelink.Equalizer(bands=[
                      wavelink.EQBand(band=0, gain=0.3),
                      wavelink.EQBand(band=1, gain=0.3),
                      wavelink.EQBand(band=2, gain=0.25),
                  ])),
    "nightcore":  wavelink.Filters(timescale=wavelink.Timescale(pitch=1.3, speed=1.3, rate=1.0)),
    "vaporwave":  wavelink.Filters(timescale=wavelink.Timescale(pitch=0.7, speed=0.8, rate=1.0)),
    "8d":         wavelink.Filters(rotation=wavelink.Rotation(rotation_hz=0.2)),
    "tremolo":    wavelink.Filters(tremolo=wavelink.Tremolo(frequency=4.0, depth=0.8)),
    "vibrato":    wavelink.Filters(vibrato=wavelink.Vibrato(frequency=4.0, depth=0.9)),
    "normalizer": wavelink.Filters(),
    "reset":      wavelink.Filters(),
}
FILTER_NAMES = list(FILTERS.keys())


class Premium(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="filter", aliases=["fx"], description="🎛️ Apply an audio filter (Premium)")
    @app_commands.describe(name="Filter name")
    @app_commands.choices(name=[app_commands.Choice(name=n.title(), value=n) for n in FILTER_NAMES])
    async def filter(self, ctx: commands.Context, name: str = None):
        if not db.has_access(ctx.guild.id, ctx.author.id):
            return await ctx.send(embed=premium_wall())
        vc = player(ctx)
        if not vc or not vc.current:
            return await ctx.send(embed=err("Nothing is playing!"))
        if not name or name.lower() not in FILTERS:
            e = discord.Embed(title="🎛️  Audio Filters", colour=cfg.COL_PREMIUM)
            e.description = " ".join(f"`{n}`" for n in FILTER_NAMES)
            e.add_field(name="Usage", value="`-filter <n>`  •  `-filter reset` to clear")
            e.set_footer(text="Zero Music • Made by Aditya</>")
            return await ctx.send(embed=e)
        await vc.set_filters(FILTERS[name.lower()])
        msg = "🎵 All filters removed." if name.lower() in ("reset", "normalizer") else f"🎛️ Applied **{name}** filter."
        await ctx.send(embed=ok(msg))

    @commands.hybrid_command(name="247", aliases=["stay"], description="🔒 Toggle 24/7 mode (Premium)")
    async def tf_seven(self, ctx: commands.Context):
        if not db.has_access(ctx.guild.id, ctx.author.id):
            return await ctx.send(embed=premium_wall())
        if not ctx.author.guild_permissions.manage_guild and ctx.author.id != cfg.OWNER_ID:
            return await ctx.send(embed=err("You need **Manage Server** permission."))
        current = db.get_settings(ctx.guild.id).get("tf_seven", False)
        db.set_setting(ctx.guild.id, "tf_seven", not current)
        msg = "🔒 **24/7 Mode ON** — I'll stay in voice even when the queue ends!" if not current \
              else "🔓 **24/7 Mode OFF** — I'll leave when the queue is empty."
        await ctx.send(embed=ok(msg))

    @commands.hybrid_command(name="djrole", description="🎧 Set or clear the DJ role (Premium)")
    @app_commands.describe(role="Role to set as DJ (omit to clear)")
    async def djrole(self, ctx: commands.Context, role: discord.Role = None):
        if not db.has_access(ctx.guild.id, ctx.author.id):
            return await ctx.send(embed=premium_wall())
        if not ctx.author.guild_permissions.manage_guild and ctx.author.id != cfg.OWNER_ID:
            return await ctx.send(embed=err("You need **Manage Server** permission."))
        if not role:
            db.set_setting(ctx.guild.id, "dj_role", None)
            return await ctx.send(embed=ok("🎧 DJ role cleared. Everyone can control music."))
        db.set_setting(ctx.guild.id, "dj_role", role.id)
        await ctx.send(embed=ok(f"🎧 **{role.name}** set as the DJ role."))

    @commands.hybrid_command(name="vote", description="🗳️ Vote on Top.gg for 12hr Premium")
    async def vote(self, ctx: commands.Context):
        await ctx.defer()
        uid = ctx.author.id
        if db.has_vote_premium(uid):
            exp  = db.vote_expiry(uid)
            mins = max(0, int((exp - time.time()) / 60))
            e = discord.Embed(title="⭐  Vote Premium Active",
                              description=f"You already have vote premium!\n**Expires in:** {mins} minute{'s' if mins!=1 else ''}",
                              colour=cfg.COL_PREMIUM)
            e.set_footer(text="Zero Music • Made by Aditya</>")
            return await ctx.send(embed=e)
        voted = await has_voted(uid)
        if voted:
            db.grant_vote_premium(uid, cfg.VOTE_HOURS)
            e = discord.Embed(
                title="✅  Vote Premium Granted!",
                description=f"Thanks for voting! You now have **{cfg.VOTE_HOURS} hours** of Premium!\n\n"
                            f"**Unlocked:**\n" + "\n".join(f"• {f}" for f in cfg.PREMIUM_FEATURES),
                colour=cfg.COL_PREMIUM,
            )
            e.set_footer(text="Zero Music • Vote again after 12h to renew • Made by Aditya</>")
            return await ctx.send(embed=e)
        e = discord.Embed(
            title="🗳️  Vote for Zero!",
            description=f"Vote for **Zero** on Top.gg to get **{cfg.VOTE_HOURS}h of free Premium**!\n\n"
                        f"**[👉 Click here to vote]({cfg.VOTE_URL})**\n\nAfter voting, run `-vote` again to claim.",
            colour=cfg.COL_PRIMARY,
        )
        e.add_field(name="⭐ What you unlock", value="\n".join(f"• {f}" for f in cfg.PREMIUM_FEATURES))
        e.set_footer(text="Zero Music • Made by Aditya</>")
        await ctx.send(embed=e)

    @commands.hybrid_command(name="premium", aliases=["prem"], description="⭐ Check or manage premium status")
    @app_commands.describe(action="Owner: grant/revoke/list/status", target="Guild ID (owner only)")
    async def premium(self, ctx: commands.Context, action: str = None, target: str = None):
        uid = ctx.author.id
        if uid == cfg.OWNER_ID:
            if action == "grant" and target:
                db.grant_premium(int(target), uid)
                return await ctx.send(embed=ok(f"⭐ Granted premium to `{target}`."))
            if action == "revoke" and target:
                db.revoke_premium(int(target))
                return await ctx.send(embed=ok(f"❌ Revoked premium from `{target}`."))
            if action == "list":
                guilds = db.all_premium_guilds()
                e = discord.Embed(title="👑  Premium Servers",
                                  description="\n".join(f"{i+1}. `{g}`" for i,g in enumerate(guilds)) or "None.",
                                  colour=cfg.COL_PREMIUM)
                e.set_footer(text=f"{len(guilds)} server(s) • Made by Aditya</>")
                return await ctx.send(embed=e)
        server = db.is_premium_guild(ctx.guild.id)
        vote   = db.has_vote_premium(uid)
        expiry = db.vote_expiry(uid)
        exp_str = f"<t:{expiry}:R>" if expiry else "N/A"
        e = discord.Embed(title="⭐  Zero Premium Status",
                          colour=cfg.COL_PREMIUM if server or vote else cfg.COL_PRIMARY)
        e.add_field(name="🏠 Server Premium", value="✅ Active" if server else "❌ Inactive", inline=True)
        e.add_field(name="🗳️ Vote Premium",
                    value=f"✅ Active (expires {exp_str})" if vote else "❌ Inactive", inline=True)
        e.add_field(name="How to get",
                    value=f"• [Vote on Top.gg]({cfg.VOTE_URL}) → {cfg.VOTE_HOURS}hr free\n• Contact bot owner for server premium",
                    inline=False)
        e.set_footer(text="Zero Music • Made by Aditya</>")
        await ctx.send(embed=e)


async def setup(bot):
    await bot.add_cog(Premium(bot))
