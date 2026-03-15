import discord
from discord.ext import commands
from discord import app_commands
import wavelink
import time
import utils.database as db
from utils.embeds import err, ok, premium_wall
from utils.topgg import has_voted
import config as cfg


def get_player(ctx) -> wavelink.Player | None:
    return ctx.guild.voice_client


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
    "normalizer": wavelink.Filters(volume=wavelink.Volume(volume=1.0)),
    "reset":      wavelink.Filters(),
}

FILTER_NAMES = ["bass", "8d", "nightcore", "vaporwave", "tremolo", "vibrato", "normalizer", "reset"]


class Premium(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── FILTER ────────────────────────────────────────────────────────────────

    @commands.command(name="filter", aliases=["filters", "fx"])
    async def filter(self, ctx: commands.Context, name: str = None):
        """Apply an audio filter (Premium)."""
        if not db.has_access(ctx.guild.id, ctx.author.id):
            return await ctx.reply(embed=premium_wall(), mention_author=False)
        player = get_player(ctx)
        if not player or not player.current:
            return await ctx.reply(embed=err("Nothing is playing!"), mention_author=False)
        if not ctx.author.voice or ctx.author.voice.channel != player.channel:
            return await ctx.reply(embed=err("You must be in the same voice channel as me!"), mention_author=False)

        if not name or name.lower() not in FILTERS:
            e = discord.Embed(
                title="🎛️  Audio Filters",
                description=" ".join(f"`{n}`" for n in FILTER_NAMES if n != "reset"),
                colour=cfg.COL_PREMIUM,
            )
            e.add_field(name="Usage", value="`-filter <name>`  •  `-filter reset` to clear")
            e.set_footer(text="Zero Music • Made by Aditya</>")
            return await ctx.reply(embed=e, mention_author=False)

        await player.set_filters(FILTERS[name.lower()])
        msg = "🎵 All filters removed." if name.lower() == "reset" else f"🎛️ Applied **{name}** filter."
        await ctx.reply(embed=ok(msg), mention_author=False)

    @app_commands.command(name="filter", description="🎛️ Apply an audio filter (Premium)")
    @app_commands.describe(name="Filter name")
    @app_commands.choices(name=[app_commands.Choice(name=n.title(), value=n) for n in FILTER_NAMES])
    async def filter_slash(self, interaction: discord.Interaction, name: str):
        ctx = await commands.Context.from_interaction(interaction)
        await self.filter(ctx, name)

    # ── 24/7 MODE ─────────────────────────────────────────────────────────────

    @commands.command(name="247", aliases=["24/7", "stay"])
    async def tf_seven(self, ctx: commands.Context):
        """Toggle 24/7 mode (Premium)."""
        if not db.has_access(ctx.guild.id, ctx.author.id):
            return await ctx.reply(embed=premium_wall(), mention_author=False)
        if not ctx.author.guild_permissions.manage_guild and ctx.author.id != cfg.OWNER_ID:
            return await ctx.reply(embed=err("You need **Manage Server** permission."), mention_author=False)
        current = db.get_settings(ctx.guild.id).get("tf_seven", False)
        db.set_setting(ctx.guild.id, "tf_seven", not current)
        if not current:
            await ctx.reply(embed=ok("🔒 **24/7 Mode ON** — I'll stay in voice even when the queue ends!"), mention_author=False)
        else:
            await ctx.reply(embed=ok("🔓 **24/7 Mode OFF** — I'll leave when the queue is empty."), mention_author=False)

    @app_commands.command(name="247", description="🔒 Toggle 24/7 mode (Premium)")
    async def tf_seven_slash(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        await self.tf_seven(ctx)

    # ── DJ ROLE ───────────────────────────────────────────────────────────────

    @commands.command(name="djrole")
    async def djrole(self, ctx: commands.Context, role: discord.Role = None):
        """Set or clear the DJ role (Premium)."""
        if not db.has_access(ctx.guild.id, ctx.author.id):
            return await ctx.reply(embed=premium_wall(), mention_author=False)
        if not ctx.author.guild_permissions.manage_guild and ctx.author.id != cfg.OWNER_ID:
            return await ctx.reply(embed=err("You need **Manage Server** permission."), mention_author=False)
        if not role:
            db.set_setting(ctx.guild.id, "dj_role", None)
            return await ctx.reply(embed=ok("🎧 DJ role cleared. Everyone can control music."), mention_author=False)
        db.set_setting(ctx.guild.id, "dj_role", role.id)
        await ctx.reply(embed=ok(f"🎧 **{role.name}** set as the DJ role."), mention_author=False)

    @app_commands.command(name="djrole", description="🎧 Set or clear the DJ role (Premium)")
    @app_commands.describe(role="Role to set as DJ (omit to clear)")
    async def djrole_slash(self, interaction: discord.Interaction, role: discord.Role = None):
        ctx = await commands.Context.from_interaction(interaction)
        await self.djrole(ctx, role)

    # ── VOTE ──────────────────────────────────────────────────────────────────

    @commands.command(name="vote")
    async def vote(self, ctx: commands.Context):
        """Vote for Zero on Top.gg for 12 hours of Premium."""
        async with ctx.typing():
            uid = ctx.author.id
            if db.has_vote_premium(uid):
                exp = db.vote_expiry(uid)
                mins = max(0, int((exp - time.time()) / 60))
                e = discord.Embed(
                    title="⭐  Vote Premium Active",
                    description=f"You already have vote premium!\n**Expires in:** {mins} minute{'s' if mins != 1 else ''}",
                    colour=cfg.COL_PREMIUM,
                )
                e.set_footer(text="Zero Music • Vote again after it expires • Made by Aditya</>")
                return await ctx.reply(embed=e, mention_author=False)

            voted = await has_voted(uid)
            if voted:
                db.grant_vote_premium(uid, cfg.VOTE_HOURS)
                e = discord.Embed(
                    title="✅  Vote Premium Granted!",
                    description=(
                        f"Thanks for voting! You now have **{cfg.VOTE_HOURS} hours** of Premium!\n\n"
                        f"**Unlocked features:**\n" + "\n".join(f"• {f}" for f in cfg.PREMIUM_FEATURES)
                    ),
                    colour=cfg.COL_PREMIUM,
                )
                e.set_footer(text="Zero Music • Vote again after 12h to renew • Made by Aditya</>")
                return await ctx.reply(embed=e, mention_author=False)

            e = discord.Embed(
                title="🗳️  Vote for Zero!",
                description=(
                    f"Vote for **Zero** on Top.gg to get **{cfg.VOTE_HOURS} hours of free Premium**!\n\n"
                    f"**[👉 Click here to vote]({cfg.VOTE_URL})**\n\n"
                    "After voting, run `-vote` again to claim your reward."
                ),
                colour=cfg.COL_PRIMARY,
            )
            e.add_field(name="⭐ What you unlock", value="\n".join(f"• {f}" for f in cfg.PREMIUM_FEATURES), inline=False)
            e.set_footer(text="Zero Music • Made by Aditya</>")
            await ctx.reply(embed=e, mention_author=False)

    @app_commands.command(name="vote", description="🗳️ Vote on Top.gg for 12hr Premium")
    async def vote_slash(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        await self.vote(ctx)

    # ── PREMIUM STATUS ────────────────────────────────────────────────────────

    @commands.command(name="premium", aliases=["prem"])
    async def premium(self, ctx: commands.Context, action: str = None, target: str = None):
        """Check premium status. Owner can also grant/revoke/list."""
        uid = ctx.author.id

        # Owner subcommands
        if uid == cfg.OWNER_ID:
            if action == "grant" and target:
                try:
                    gid = int(target)
                except ValueError:
                    return await ctx.reply(embed=err("Invalid guild ID."), mention_author=False)
                db.grant_premium(gid, uid)
                return await ctx.reply(embed=ok(f"⭐ Granted premium to server `{gid}`."), mention_author=False)
            if action == "revoke" and target:
                try:
                    gid = int(target)
                except ValueError:
                    return await ctx.reply(embed=err("Invalid guild ID."), mention_author=False)
                db.revoke_premium(gid)
                return await ctx.reply(embed=ok(f"❌ Revoked premium from `{gid}`."), mention_author=False)
            if action == "list":
                guilds = db.all_premium_guilds()
                e = discord.Embed(
                    title="👑  Premium Servers",
                    description="\n".join(f"{i+1}. `{g}`" for i, g in enumerate(guilds)) or "None.",
                    colour=cfg.COL_PREMIUM,
                )
                e.set_footer(text=f"{len(guilds)} server(s) • Made by Aditya</>")
                return await ctx.reply(embed=e, mention_author=False)
            if action == "status" and target:
                info = db.get_premium_info(int(target))
                e = discord.Embed(
                    title=f"Server `{target}` Premium",
                    colour=cfg.COL_PREMIUM if info and info.get("active") else cfg.COL_ERROR,
                )
                e.add_field(name="Status",     value="✅ Active" if info and info.get("active") else "❌ Inactive", inline=True)
                e.add_field(name="Granted by", value=str(info.get("granted_by", "N/A")) if info else "N/A",          inline=True)
                e.set_footer(text="Made by Aditya</>")
                return await ctx.reply(embed=e, mention_author=False)

        # User status
        server_prem = db.is_premium_guild(ctx.guild.id)
        vote_prem   = db.has_vote_premium(uid)
        expiry      = db.vote_expiry(uid)
        exp_str     = f"<t:{expiry}:R>" if expiry else "N/A"

        e = discord.Embed(
            title="⭐  Zero Premium Status",
            colour=cfg.COL_PREMIUM if server_prem or vote_prem else cfg.COL_PRIMARY,
        )
        e.add_field(name="🏠 Server Premium", value="✅ Active" if server_prem else "❌ Not active", inline=True)
        e.add_field(name="🗳️ Vote Premium",   value=f"✅ Active (expires {exp_str})" if vote_prem else "❌ Not active", inline=True)
        e.add_field(
            name="How to get Premium",
            value=f"• [Vote on Top.gg]({cfg.VOTE_URL}) → {cfg.VOTE_HOURS}hr free\n• Contact bot owner for server premium",
            inline=False,
        )
        e.set_footer(text="Zero Music • Made by Aditya</>")
        await ctx.reply(embed=e, mention_author=False)

    @app_commands.command(name="premium", description="⭐ Check your premium status")
    async def premium_slash(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        await self.premium(ctx)


async def setup(bot):
    await bot.add_cog(Premium(bot))
