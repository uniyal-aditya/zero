import discord
from discord.ext import commands
from discord import app_commands
import time
import platform
import psutil
import os
import config as cfg

# track bot start time for uptime
START_TIME = time.time()


def _uptime() -> str:
    delta = int(time.time() - START_TIME)
    d, r  = divmod(delta, 86400)
    h, r  = divmod(r, 3600)
    m, s  = divmod(r, 60)
    parts = []
    if d: parts.append(f"{d}d")
    if h: parts.append(f"{h}h")
    if m: parts.append(f"{m}m")
    parts.append(f"{s}s")
    return " ".join(parts)


def _badge_str(user: discord.User | discord.Member) -> str:
    if not hasattr(user, "public_flags") or not user.public_flags:
        return "None"
    flag_map = {
        "staff":                    "👮 Discord Staff",
        "partner":                  "🤝 Partner",
        "hypesquad":                "🏠 HypeSquad Events",
        "bug_hunter":               "🐛 Bug Hunter",
        "hypesquad_bravery":        "🟣 Bravery",
        "hypesquad_brilliance":     "🔴 Brilliance",
        "hypesquad_balance":        "🟡 Balance",
        "early_supporter":          "👑 Early Supporter",
        "bug_hunter_level_2":       "🐛 Bug Hunter Lv2",
        "verified_bot_developer":   "🤖 Verified Bot Dev",
        "active_developer":         "🛠️ Active Developer",
    }
    badges = [label for attr, label in flag_map.items() if getattr(user.public_flags, attr, False)]
    return "  ".join(badges) if badges else "None"


def _status_emoji(status: discord.Status) -> str:
    return {
        discord.Status.online:    "🟢 Online",
        discord.Status.idle:      "🌙 Idle",
        discord.Status.dnd:       "🔴 Do Not Disturb",
        discord.Status.offline:   "⚫ Offline",
    }.get(status, "⚫ Offline")


class General(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── PING ─────────────────────────────────────────────────────────────────

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        """Check the bot's latency."""
        before = time.monotonic()
        msg = await ctx.reply(
            embed=discord.Embed(description="🏓 Pinging…", colour=cfg.COL_PRIMARY),
            mention_author=False,
        )
        after = time.monotonic()
        rtt   = round((after - before) * 1000)
        ws    = round(self.bot.latency * 1000)

        colour = cfg.COL_SUCCESS if ws < 100 else cfg.COL_WARNING if ws < 200 else cfg.COL_ERROR
        bar_ws = "▰" * min(10, ws // 20) + "▱" * max(0, 10 - ws // 20)

        e = discord.Embed(title="🏓  Pong!", colour=colour)
        e.add_field(name="💓 WebSocket",    value=f"`{ws} ms`  {bar_ws}", inline=True)
        e.add_field(name="📨 Round-trip",   value=f"`{rtt} ms`",          inline=True)
        e.add_field(name="⏱ Uptime",        value=_uptime(),               inline=True)
        e.set_footer(text="Zero Music • Made by Aditya</>")
        await msg.edit(embed=e)

    @app_commands.command(name="ping", description="🏓 Check the bot's latency")
    async def ping_slash(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        await self.ping(ctx)

    # ── STATS ─────────────────────────────────────────────────────────────────

    @commands.command(name="stats", aliases=["botstats", "botinfo", "about"])
    async def stats(self, ctx: commands.Context):
        """Show detailed bot statistics."""
        bot = self.bot
        total_members = sum(g.member_count or 0 for g in bot.guilds)

        # Try to get memory usage
        try:
            proc    = psutil.Process(os.getpid())
            mem_mb  = proc.memory_info().rss / 1024 / 1024
            cpu_pct = psutil.cpu_percent(interval=None)
            sys_str = f"RAM: `{mem_mb:.1f} MB`\nCPU: `{cpu_pct:.1f}%`"
        except Exception:
            sys_str = "N/A"

        e = discord.Embed(
            title="🎵  Zero Music Bot — Stats",
            description=(
                "A high-definition music bot packed with every feature you need.\n"
                f"[Support Server]({cfg.SUPPORT_URL})  •  [Invite Me]({cfg.INVITE_URL})"
            ),
            colour=cfg.COL_PRIMARY,
        )
        if bot.user and bot.user.avatar:
            e.set_thumbnail(url=bot.user.avatar.url)

        e.add_field(name="🌐 Servers",      value=f"`{len(bot.guilds)}`",            inline=True)
        e.add_field(name="👥 Users",        value=f"`{total_members:,}`",            inline=True)
        e.add_field(name="💓 Ping",         value=f"`{round(bot.latency*1000)} ms`", inline=True)
        e.add_field(name="⏱ Uptime",        value=_uptime(),                         inline=True)
        e.add_field(name="🐍 Python",       value=f"`{platform.python_version()}`",  inline=True)
        e.add_field(name="📦 discord.py",   value=f"`{discord.__version__}`",        inline=True)
        e.add_field(name="🖥️ System",       value=sys_str,                           inline=True)
        e.add_field(name="👑 Owner",        value=f"<@{cfg.OWNER_ID}>",              inline=True)
        e.add_field(name="🛠 Version",      value=f"`{cfg.BOT_VERSION}`",            inline=True)

        e.set_footer(text="Zero Music • Made by Aditya</>")
        await ctx.reply(embed=e, mention_author=False)

    @app_commands.command(name="stats", description="📊 Show detailed bot statistics")
    async def stats_slash(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        await self.stats(ctx)

    # ── SERVER INFO ───────────────────────────────────────────────────────────

    @commands.command(name="serverinfo", aliases=["si", "guildinfo", "server"])
    async def serverinfo(self, ctx: commands.Context):
        """Display information about this server."""
        g = ctx.guild

        # Role & channel counts
        text_ch   = len([c for c in g.channels if isinstance(c, discord.TextChannel)])
        voice_ch  = len([c for c in g.channels if isinstance(c, discord.VoiceChannel)])
        cats      = len(g.categories)
        bots      = sum(1 for m in g.members if m.bot)
        humans    = g.member_count - bots

        # Verification label
        ver_map = {
            discord.VerificationLevel.none:    "None",
            discord.VerificationLevel.low:     "Low",
            discord.VerificationLevel.medium:  "Medium",
            discord.VerificationLevel.high:    "High",
            discord.VerificationLevel.highest: "Highest",
        }

        # Boost status
        boost_str = f"Level {g.premium_tier} ({g.premium_subscription_count} boosts)"

        e = discord.Embed(
            title=f"🏠  {g.name}",
            colour=cfg.COL_PRIMARY,
        )
        if g.icon:
            e.set_thumbnail(url=g.icon.url)
        if g.banner:
            e.set_image(url=g.banner.with_format("png").url)

        e.add_field(name="🆔 Server ID",        value=f"`{g.id}`",                         inline=True)
        e.add_field(name="👑 Owner",             value=f"<@{g.owner_id}>",                  inline=True)
        e.add_field(name="🌍 Region",            value=str(g.preferred_locale),             inline=True)
        e.add_field(name="📅 Created",           value=f"<t:{int(g.created_at.timestamp())}:D> (<t:{int(g.created_at.timestamp())}:R>)", inline=False)
        e.add_field(name="👥 Members",           value=f"Total: `{g.member_count}`\nHumans: `{humans}`\nBots: `{bots}`", inline=True)
        e.add_field(name="💬 Channels",          value=f"Text: `{text_ch}`\nVoice: `{voice_ch}`\nCategories: `{cats}`", inline=True)
        e.add_field(name="🎭 Roles",             value=f"`{len(g.roles)}`",                 inline=True)
        e.add_field(name="🔒 Verification",      value=ver_map.get(g.verification_level, "?"), inline=True)
        e.add_field(name="🚀 Boost Status",      value=boost_str,                            inline=True)
        e.add_field(name="😀 Emojis",            value=f"`{len(g.emojis)}`",                inline=True)

        e.set_footer(text=f"Zero Music • Made by Aditya</>  •  Requested by {ctx.author.display_name}")
        await ctx.reply(embed=e, mention_author=False)

    @app_commands.command(name="serverinfo", description="🏠 Show information about this server")
    async def serverinfo_slash(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        await self.serverinfo(ctx)

    # ── USER INFO ─────────────────────────────────────────────────────────────

    @commands.command(name="userinfo", aliases=["ui", "whois", "user"])
    async def userinfo(self, ctx: commands.Context, member: discord.Member = None):
        """Display information about a user."""
        member = member or ctx.author
        user   = await self.bot.fetch_user(member.id)   # fetch for banner

        roles = [r.mention for r in reversed(member.roles) if r.name != "@everyone"]
        roles_str = " ".join(roles[:15]) + (f" +{len(roles)-15} more" if len(roles) > 15 else "") if roles else "None"

        joined_pos = sorted(ctx.guild.members, key=lambda m: m.joined_at or discord.utils.utcnow()).index(member) + 1

        e = discord.Embed(
            title=f"👤  {member}",
            colour=member.colour if member.colour.value else cfg.COL_PRIMARY,
        )
        e.set_thumbnail(url=member.display_avatar.url)
        if user.banner:
            e.set_image(url=user.banner.with_format("png").url)

        e.add_field(name="🆔 User ID",         value=f"`{member.id}`",                                          inline=True)
        e.add_field(name="📛 Display Name",    value=member.display_name,                                       inline=True)
        e.add_field(name="🤖 Bot",             value="Yes" if member.bot else "No",                              inline=True)
        e.add_field(name="📅 Account Created", value=f"<t:{int(member.created_at.timestamp())}:D> (<t:{int(member.created_at.timestamp())}:R>)", inline=False)
        e.add_field(name="📥 Joined Server",   value=f"<t:{int(member.joined_at.timestamp())}:D> (<t:{int(member.joined_at.timestamp())}:R>)\nJoin position: `#{joined_pos}`", inline=False)
        e.add_field(name="🔮 Status",          value=_status_emoji(member.status),                              inline=True)
        e.add_field(name="🏅 Badges",          value=_badge_str(member),                                        inline=True)
        e.add_field(name="🎭 Top Role",        value=member.top_role.mention,                                   inline=True)
        e.add_field(name=f"🎭 Roles [{len(roles)}]", value=roles_str,                                           inline=False)

        e.set_footer(text=f"Zero Music • Made by Aditya</>  •  Requested by {ctx.author.display_name}")
        await ctx.reply(embed=e, mention_author=False)

    @app_commands.command(name="userinfo", description="👤 Show information about a user")
    @app_commands.describe(member="User to look up (defaults to you)")
    async def userinfo_slash(self, interaction: discord.Interaction, member: discord.Member = None):
        ctx = await commands.Context.from_interaction(interaction)
        await self.userinfo(ctx, member)

    # ── AVATAR ────────────────────────────────────────────────────────────────

    @commands.command(name="avatar", aliases=["av", "pfp"])
    async def avatar(self, ctx: commands.Context, member: discord.Member = None):
        """Show a user's avatar."""
        member = member or ctx.author
        e = discord.Embed(
            title=f"🖼️  {member.display_name}'s Avatar",
            colour=cfg.COL_PRIMARY,
        )
        e.set_image(url=member.display_avatar.with_size(1024).url)
        links = " | ".join(
            f"[{fmt.upper()}]({member.display_avatar.with_format(fmt).url})"  # type: ignore
            for fmt in ("png", "jpg", "webp")
        )
        e.set_footer(text=f"Download: {links}  •  Made by Aditya</>")
        await ctx.reply(embed=e, mention_author=False)

    @app_commands.command(name="avatar", description="🖼️ Show a user's avatar")
    @app_commands.describe(member="User to show avatar of")
    async def avatar_slash(self, interaction: discord.Interaction, member: discord.Member = None):
        ctx = await commands.Context.from_interaction(interaction)
        await self.avatar(ctx, member)

    # ── BANNER ────────────────────────────────────────────────────────────────

    @commands.command(name="banner")
    async def banner(self, ctx: commands.Context, member: discord.Member = None):
        """Show a user's banner."""
        member = member or ctx.author
        user   = await self.bot.fetch_user(member.id)
        if not user.banner:
            return await ctx.reply(
                embed=discord.Embed(description=f"❌  **{member.display_name}** has no banner.", colour=cfg.COL_ERROR),
                mention_author=False,
            )
        e = discord.Embed(title=f"🖼️  {member.display_name}'s Banner", colour=cfg.COL_PRIMARY)
        e.set_image(url=user.banner.with_size(1024).url)
        e.set_footer(text="Zero Music • Made by Aditya</>")
        await ctx.reply(embed=e, mention_author=False)

    @app_commands.command(name="banner", description="🖼️ Show a user's profile banner")
    @app_commands.describe(member="User to show banner of")
    async def banner_slash(self, interaction: discord.Interaction, member: discord.Member = None):
        ctx = await commands.Context.from_interaction(interaction)
        await self.banner(ctx, member)

    # ── INVITE ────────────────────────────────────────────────────────────────

    @commands.command(name="invite", aliases=["inv", "addbot"])
    async def invite(self, ctx: commands.Context):
        """Get Zero's invite link."""
        e = discord.Embed(
            title="➕  Invite Zero to your server!",
            description=(
                f"[**🔗 Click here to invite Zero**]({cfg.INVITE_URL})\n\n"
                "Add the best HD music bot to your server and enjoy crystal-clear audio, "
                "playlists, liked songs, premium features and more!"
            ),
            colour=cfg.COL_PRIMARY,
        )
        if self.bot.user and self.bot.user.avatar:
            e.set_thumbnail(url=self.bot.user.avatar.url)
        e.add_field(name="🎵 Features",
                    value="YouTube • Spotify • Playlists\nLiked Songs • Filters • 24/7 • HD Audio",
                    inline=False)
        e.set_footer(text="Zero Music • Made by Aditya</>")

        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Invite Zero", url=cfg.INVITE_URL, emoji="➕"))
        view.add_item(discord.ui.Button(label="Support Server", url=cfg.SUPPORT_URL, emoji="💬"))
        await ctx.reply(embed=e, view=view, mention_author=False)

    @app_commands.command(name="invite", description="➕ Get Zero's invite link")
    async def invite_slash(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        await self.invite(ctx)

    # ── SUPPORT ───────────────────────────────────────────────────────────────

    @commands.command(name="support", aliases=["server", "discord"])
    async def support(self, ctx: commands.Context):
        """Get the link to Zero's support server."""
        e = discord.Embed(
            title="💬  Zero Support Server",
            description=(
                f"Need help? Found a bug? Want to suggest a feature?\n\n"
                f"**[Join our support server!]({cfg.SUPPORT_URL})**"
            ),
            colour=cfg.COL_PRIMARY,
        )
        e.set_footer(text="Zero Music • Made by Aditya</>")
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Join Support Server", url=cfg.SUPPORT_URL, emoji="💬"))
        view.add_item(discord.ui.Button(label="Invite Zero", url=cfg.INVITE_URL, emoji="➕"))
        await ctx.reply(embed=e, view=view, mention_author=False)

    @app_commands.command(name="support", description="💬 Get the Zero support server link")
    async def support_slash(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        await self.support(ctx)

    # ── ROLEINFO ──────────────────────────────────────────────────────────────

    @commands.command(name="roleinfo", aliases=["ri", "role"])
    async def roleinfo(self, ctx: commands.Context, *, role: discord.Role = None):
        """Show information about a role."""
        if not role:
            return await ctx.reply(
                embed=discord.Embed(description="❌  Mention or name a role.", colour=cfg.COL_ERROR),
                mention_author=False,
            )
        perms = [p.replace("_", " ").title() for p, v in role.permissions if v]
        perm_str = ", ".join(perms[:10]) + (f"… +{len(perms)-10} more" if len(perms) > 10 else "") if perms else "None"
        members_with_role = len(role.members)

        e = discord.Embed(title=f"🎭  Role: {role.name}", colour=role.colour if role.colour.value else cfg.COL_PRIMARY)
        e.add_field(name="🆔 Role ID",       value=f"`{role.id}`",                                         inline=True)
        e.add_field(name="🎨 Colour",        value=str(role.colour),                                       inline=True)
        e.add_field(name="📍 Position",      value=f"`{role.position}`",                                   inline=True)
        e.add_field(name="👥 Members",       value=f"`{members_with_role}`",                               inline=True)
        e.add_field(name="📣 Mentionable",   value="Yes" if role.mentionable else "No",                    inline=True)
        e.add_field(name="📌 Hoisted",       value="Yes" if role.hoist else "No",                          inline=True)
        e.add_field(name="📅 Created",       value=f"<t:{int(role.created_at.timestamp())}:D>",            inline=False)
        e.add_field(name="🔑 Key Perms",     value=perm_str,                                               inline=False)
        e.set_footer(text="Zero Music • Made by Aditya</>")
        await ctx.reply(embed=e, mention_author=False)

    @app_commands.command(name="roleinfo", description="🎭 Show information about a role")
    @app_commands.describe(role="The role to look up")
    async def roleinfo_slash(self, interaction: discord.Interaction, role: discord.Role):
        ctx = await commands.Context.from_interaction(interaction)
        await self.roleinfo(ctx, role=role)

    # ── BOTINFO ───────────────────────────────────────────────────────────────

    @commands.command(name="botinfo", aliases=["bot", "info"])
    async def botinfo(self, ctx: commands.Context):
        """Show info about Zero."""
        bot = self.bot
        e = discord.Embed(
            title="🎵  Zero Music Bot",
            description=(
                "A feature-rich, high-definition Discord music bot.\n\n"
                f"[Support]({cfg.SUPPORT_URL})  •  [Invite]({cfg.INVITE_URL})  •  [Vote](https://top.gg/bot/{cfg.CLIENT_ID}/vote)"
            ),
            colour=cfg.COL_PRIMARY,
        )
        if bot.user and bot.user.avatar:
            e.set_thumbnail(url=bot.user.avatar.url)
        e.add_field(name="🆔 Bot ID",       value=f"`{cfg.CLIENT_ID}`",              inline=True)
        e.add_field(name="👑 Owner",        value=f"<@{cfg.OWNER_ID}>",              inline=True)
        e.add_field(name="🛠 Version",      value=f"`{cfg.BOT_VERSION}`",            inline=True)
        e.add_field(name="🌐 Servers",      value=f"`{len(bot.guilds)}`",            inline=True)
        e.add_field(name="💓 Ping",         value=f"`{round(bot.latency*1000)} ms`", inline=True)
        e.add_field(name="⏱ Uptime",        value=_uptime(),                         inline=True)
        e.add_field(name="🎵 Prefix",       value=f"`{cfg.PREFIX}`  +  `/` slash",  inline=True)
        e.add_field(name="🐍 Python",       value=f"`{platform.python_version()}`",  inline=True)
        e.add_field(name="📦 discord.py",   value=f"`{discord.__version__}`",        inline=True)
        e.add_field(
            name="✨ Features",
            value="YouTube • Spotify • Playlists • Liked Songs\nAudio Filters • 24/7 • Premium • HD Audio",
            inline=False,
        )
        e.set_footer(text="Zero Music • Made by Aditya</>")

        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Support Server", url=cfg.SUPPORT_URL,  emoji="💬"))
        view.add_item(discord.ui.Button(label="Invite Zero",    url=cfg.INVITE_URL,   emoji="➕"))
        view.add_item(discord.ui.Button(label="Vote on Top.gg", url=f"https://top.gg/bot/{cfg.CLIENT_ID}/vote", emoji="⭐"))
        await ctx.reply(embed=e, view=view, mention_author=False)

    @app_commands.command(name="botinfo", description="🎵 Show information about Zero")
    async def botinfo_slash(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        await self.botinfo(ctx)


async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))
