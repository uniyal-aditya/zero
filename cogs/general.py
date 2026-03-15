import discord
from discord.ext import commands
from discord import app_commands
import time, platform, psutil, os
import config as cfg

START_TIME = time.time()

def _uptime():
    d = int(time.time() - START_TIME)
    h, r = divmod(d, 3600)
    m, s = divmod(r, 60)
    parts = []
    if h: parts.append(f"{h}h")
    if m: parts.append(f"{m}m")
    parts.append(f"{s}s")
    return " ".join(parts)

def _status_emoji(status):
    return {discord.Status.online:"🟢 Online", discord.Status.idle:"🌙 Idle",
            discord.Status.dnd:"🔴 DnD", discord.Status.offline:"⚫ Offline"}.get(status,"⚫ Offline")


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="ping", description="🏓 Check bot latency")
    async def ping(self, ctx: commands.Context):
        before = time.monotonic()
        msg = await ctx.send(embed=discord.Embed(description="🏓 Pinging…", colour=cfg.COL_PRIMARY))
        rtt = round((time.monotonic() - before) * 1000)
        ws  = round(self.bot.latency * 1000)
        col = cfg.COL_SUCCESS if ws < 100 else cfg.COL_WARNING if ws < 200 else cfg.COL_ERROR
        e = discord.Embed(title="🏓  Pong!", colour=col)
        e.add_field(name="💓 WebSocket",  value=f"`{ws} ms`",  inline=True)
        e.add_field(name="📨 Round-trip", value=f"`{rtt} ms`", inline=True)
        e.add_field(name="⏱ Uptime",      value=_uptime(),     inline=True)
        e.set_footer(text="Zero Music • Made by Aditya</>")
        await msg.edit(embed=e)

    @commands.hybrid_command(name="stats", aliases=["botstats"], description="📊 Show bot statistics")
    async def stats(self, ctx: commands.Context):
        total = sum(g.member_count or 0 for g in self.bot.guilds)
        try:
            proc = psutil.Process(os.getpid())
            mem  = proc.memory_info().rss / 1024 / 1024
            sys_str = f"RAM: `{mem:.1f} MB`"
        except Exception:
            sys_str = "N/A"
        e = discord.Embed(
            title="🎵  Zero Music Bot — Stats",
            description=f"A high-definition music bot.\n[Support]({cfg.SUPPORT_URL})  •  [Invite]({cfg.INVITE_URL})",
            colour=cfg.COL_PRIMARY,
        )
        if self.bot.user and self.bot.user.avatar:
            e.set_thumbnail(url=self.bot.user.avatar.url)
        e.add_field(name="🌐 Servers",    value=f"`{len(self.bot.guilds)}`",            inline=True)
        e.add_field(name="👥 Users",      value=f"`{total:,}`",                         inline=True)
        e.add_field(name="💓 Ping",       value=f"`{round(self.bot.latency*1000)} ms`", inline=True)
        e.add_field(name="⏱ Uptime",      value=_uptime(),                              inline=True)
        e.add_field(name="🐍 Python",     value=f"`{platform.python_version()}`",       inline=True)
        e.add_field(name="🖥️ System",     value=sys_str,                                inline=True)
        e.add_field(name="👑 Owner",      value=f"<@{cfg.OWNER_ID}>",                   inline=True)
        e.add_field(name="🛠 Version",    value=f"`{cfg.BOT_VERSION}`",                 inline=True)
        e.set_footer(text="Zero Music • Made by Aditya</>")
        await ctx.send(embed=e)

    @commands.hybrid_command(name="botinfo", aliases=["bot", "info"], description="🎵 Show info about Zero")
    async def botinfo(self, ctx: commands.Context):
        e = discord.Embed(
            title="🎵  Zero Music Bot",
            description=f"A feature-rich HD music bot.\n[Support]({cfg.SUPPORT_URL})  •  [Invite]({cfg.INVITE_URL})  •  [Vote](https://top.gg/bot/{cfg.CLIENT_ID}/vote)",
            colour=cfg.COL_PRIMARY,
        )
        if self.bot.user and self.bot.user.avatar:
            e.set_thumbnail(url=self.bot.user.avatar.url)
        e.add_field(name="🆔 Bot ID",    value=f"`{cfg.CLIENT_ID}`",              inline=True)
        e.add_field(name="👑 Owner",     value=f"<@{cfg.OWNER_ID}>",              inline=True)
        e.add_field(name="⏱ Uptime",     value=_uptime(),                         inline=True)
        e.add_field(name="🌐 Servers",   value=f"`{len(self.bot.guilds)}`",       inline=True)
        e.add_field(name="💓 Ping",      value=f"`{round(self.bot.latency*1000)} ms`", inline=True)
        e.add_field(name="🎵 Prefix",    value=f"`{cfg.PREFIX}`  +  `/` slash",  inline=True)
        e.set_footer(text="Zero Music • Made by Aditya</>")
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Support", url=cfg.SUPPORT_URL, emoji="💬"))
        view.add_item(discord.ui.Button(label="Invite",  url=cfg.INVITE_URL,  emoji="➕"))
        view.add_item(discord.ui.Button(label="Vote",    url=f"https://top.gg/bot/{cfg.CLIENT_ID}/vote", emoji="⭐"))
        await ctx.send(embed=e, view=view)

    @commands.hybrid_command(name="serverinfo", aliases=["si"], description="🏠 Show server information")
    async def serverinfo(self, ctx: commands.Context):
        g = ctx.guild
        text  = len([c for c in g.channels if isinstance(c, discord.TextChannel)])
        voice = len([c for c in g.channels if isinstance(c, discord.VoiceChannel)])
        bots  = sum(1 for m in g.members if m.bot)
        e = discord.Embed(title=f"🏠  {g.name}", colour=cfg.COL_PRIMARY)
        if g.icon:
            e.set_thumbnail(url=g.icon.url)
        e.add_field(name="🆔 Server ID",   value=f"`{g.id}`",                      inline=True)
        e.add_field(name="👑 Owner",        value=f"<@{g.owner_id}>",               inline=True)
        e.add_field(name="📅 Created",      value=f"<t:{int(g.created_at.timestamp())}:D>", inline=True)
        e.add_field(name="👥 Members",      value=f"Total: `{g.member_count}`\nBots: `{bots}`", inline=True)
        e.add_field(name="💬 Channels",     value=f"Text: `{text}`  Voice: `{voice}`", inline=True)
        e.add_field(name="🎭 Roles",        value=f"`{len(g.roles)}`",              inline=True)
        e.add_field(name="🚀 Boosts",       value=f"Level `{g.premium_tier}` ({g.premium_subscription_count} boosts)", inline=True)
        e.set_footer(text=f"Zero Music • Made by Aditya</>  •  Requested by {ctx.author.display_name}")
        await ctx.send(embed=e)

    @commands.hybrid_command(name="userinfo", aliases=["ui", "whois"], description="👤 Show user information")
    @app_commands.describe(member="User to look up (defaults to you)")
    async def userinfo(self, ctx: commands.Context, member: discord.Member = None):
        member = member or ctx.author
        roles  = [r.mention for r in reversed(member.roles) if r.name != "@everyone"]
        roles_str = " ".join(roles[:12]) + (f" +{len(roles)-12} more" if len(roles)>12 else "") if roles else "None"
        e = discord.Embed(title=f"👤  {member}", colour=member.colour if member.colour.value else cfg.COL_PRIMARY)
        e.set_thumbnail(url=member.display_avatar.url)
        e.add_field(name="🆔 User ID",       value=f"`{member.id}`",       inline=True)
        e.add_field(name="🤖 Bot",           value="Yes" if member.bot else "No", inline=True)
        e.add_field(name="🔮 Status",        value=_status_emoji(member.status), inline=True)
        e.add_field(name="📅 Account Created", value=f"<t:{int(member.created_at.timestamp())}:D> (<t:{int(member.created_at.timestamp())}:R>)", inline=False)
        e.add_field(name="📥 Joined Server",   value=f"<t:{int(member.joined_at.timestamp())}:D> (<t:{int(member.joined_at.timestamp())}:R>)", inline=False)
        e.add_field(name="🎭 Top Role",      value=member.top_role.mention, inline=True)
        e.add_field(name=f"🎭 Roles [{len(roles)}]", value=roles_str, inline=False)
        e.set_footer(text=f"Zero Music • Made by Aditya</>  •  Requested by {ctx.author.display_name}")
        await ctx.send(embed=e)

    @commands.hybrid_command(name="avatar", aliases=["av", "pfp"], description="🖼️ Show a user's avatar")
    @app_commands.describe(member="User to show avatar of")
    async def avatar(self, ctx: commands.Context, member: discord.Member = None):
        member = member or ctx.author
        e = discord.Embed(title=f"🖼️  {member.display_name}'s Avatar", colour=cfg.COL_PRIMARY)
        e.set_image(url=member.display_avatar.with_size(1024).url)
        e.set_footer(text="Zero Music • Made by Aditya</>")
        await ctx.send(embed=e)

    @commands.hybrid_command(name="banner", description="🖼️ Show a user's profile banner")
    @app_commands.describe(member="User to show banner of")
    async def banner(self, ctx: commands.Context, member: discord.Member = None):
        member = member or ctx.author
        user   = await self.bot.fetch_user(member.id)
        if not user.banner:
            return await ctx.send(embed=discord.Embed(
                description=f"❌  **{member.display_name}** has no banner.", colour=cfg.COL_ERROR))
        e = discord.Embed(title=f"🖼️  {member.display_name}'s Banner", colour=cfg.COL_PRIMARY)
        e.set_image(url=user.banner.with_size(1024).url)
        e.set_footer(text="Zero Music • Made by Aditya</>")
        await ctx.send(embed=e)

    @commands.hybrid_command(name="invite", aliases=["inv"], description="➕ Get Zero's invite link")
    async def invite(self, ctx: commands.Context):
        e = discord.Embed(
            title="➕  Invite Zero!",
            description=f"[**Click here to invite Zero**]({cfg.INVITE_URL})\n\nYouTube • Spotify • Playlists • HD Audio",
            colour=cfg.COL_PRIMARY,
        )
        if self.bot.user and self.bot.user.avatar:
            e.set_thumbnail(url=self.bot.user.avatar.url)
        e.set_footer(text="Zero Music • Made by Aditya</>")
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Invite Zero",    url=cfg.INVITE_URL,   emoji="➕"))
        view.add_item(discord.ui.Button(label="Support Server", url=cfg.SUPPORT_URL,  emoji="💬"))
        await ctx.send(embed=e, view=view)

    @commands.hybrid_command(name="support", aliases=["server"], description="💬 Get the support server link")
    async def support(self, ctx: commands.Context):
        e = discord.Embed(
            title="💬  Zero Support Server",
            description=f"Need help? [**Join our support server!**]({cfg.SUPPORT_URL})",
            colour=cfg.COL_PRIMARY,
        )
        e.set_footer(text="Zero Music • Made by Aditya</>")
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Join Support", url=cfg.SUPPORT_URL, emoji="💬"))
        view.add_item(discord.ui.Button(label="Invite Zero",  url=cfg.INVITE_URL,  emoji="➕"))
        await ctx.send(embed=e, view=view)

    @commands.hybrid_command(name="roleinfo", aliases=["ri"], description="🎭 Show information about a role")
    @app_commands.describe(role="The role to look up")
    async def roleinfo(self, ctx: commands.Context, *, role: discord.Role):
        perms = [p.replace("_"," ").title() for p,v in role.permissions if v]
        perm_str = ", ".join(perms[:10]) + (f"… +{len(perms)-10} more" if len(perms)>10 else "") if perms else "None"
        e = discord.Embed(title=f"🎭  {role.name}", colour=role.colour if role.colour.value else cfg.COL_PRIMARY)
        e.add_field(name="🆔 ID",         value=f"`{role.id}`",                           inline=True)
        e.add_field(name="🎨 Colour",     value=str(role.colour),                         inline=True)
        e.add_field(name="👥 Members",    value=f"`{len(role.members)}`",                 inline=True)
        e.add_field(name="📌 Hoisted",    value="Yes" if role.hoist else "No",            inline=True)
        e.add_field(name="📣 Mentionable",value="Yes" if role.mentionable else "No",      inline=True)
        e.add_field(name="📅 Created",    value=f"<t:{int(role.created_at.timestamp())}:D>", inline=True)
        e.add_field(name="🔑 Key Perms",  value=perm_str,                                 inline=False)
        e.set_footer(text="Zero Music • Made by Aditya</>")
        await ctx.send(embed=e)


async def setup(bot):
    await bot.add_cog(General(bot))
