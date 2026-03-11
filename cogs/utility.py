# cogs/utility.py
import time, discord, platform, os
from discord.ext import commands
import config
from core.votes import check_vote_topgg, _vote_url

PREMIUM_INFO = """
**Zero Premium** unlocks extra features for your server:

🔀 **Shuffle** — shuffle the queue
⏭ **Skip to position** — `.skipto <pos>`
🔁 **Queue loop** — loop the entire queue
🎛 **Audio filters** — bassboost, nightcore, vaporwave & more
📍 **24/7 mode** — bot stays in VC even when queue is empty

**How to get Premium:**
Contact the bot owner to get premium added to your server.
Once granted, all premium features unlock server-wide.
"""

GUIDE_TEXT = """
**Getting Started with Zero 🎵**

**1. Join a voice channel** then use:
`.play <song name or YouTube URL>` — plays instantly

**2. Search for music:**
`.search <query>` — shows 5 results to pick from

**3. Queue management:**
`.queue` — see what's up next
`.skip` — skip current track
`.remove <pos>` — remove a track
`.move <from> <to>` — reorder tracks

**4. Playlists:**
`.pl create <name>` — create a playlist
`.pl add <name>` — save current song
`.pl play <name>` — queue the whole playlist

**5. Liked Songs:**
`.like` — like current track
`.likedplay` — queue all liked songs

**6. Controls:**
`.pause` / `.resume` — pause/resume
`.volume <0-200>` — set volume
`.loop` — cycle loop modes
`.np` — see current track

**Need more help?** Use `.help` for all commands.
"""

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()

    @commands.command(name="ping", aliases=["latency"])
    async def ping(self, ctx: commands.Context):
        """Check the bot's latency."""
        ws = round(self.bot.latency * 1000)
        color = 0x2ecc71 if ws < 100 else 0xe67e22 if ws < 200 else 0xe74c3c
        embed = discord.Embed(title="🏓 Pong!", color=color)
        embed.add_field(name="WebSocket", value=f"`{ws}ms`")
        await ctx.send(embed=embed)

    @commands.command(name="uptime")
    async def uptime(self, ctx: commands.Context):
        """Show how long Zero has been running."""
        diff = int(time.time() - self.start_time)
        h, r = divmod(diff, 3600)
        m, s = divmod(r, 60)
        d, h = divmod(h, 24)
        parts = []
        if d: parts.append(f"{d}d")
        if h: parts.append(f"{h}h")
        if m: parts.append(f"{m}m")
        parts.append(f"{s}s")
        embed = discord.Embed(title="⏱ Uptime", description=" ".join(parts), color=0x5865F2)
        await ctx.send(embed=embed)

    @commands.command(name="invite")
    async def invite(self, ctx: commands.Context):
        """Get the invite link for Zero."""
        app_id = self.bot.application_id
        if app_id:
            url = f"https://discord.com/oauth2/authorize?client_id={app_id}&scope=bot+applications.commands&permissions=8"
            embed = discord.Embed(title="📨 Invite Zero", description=f"[Click here to invite Zero]({url})", color=0x5865F2)
        else:
            embed = discord.Embed(title="📨 Invite Zero", description="Invite link not available.", color=0xff0000)
        await ctx.send(embed=embed)

    @commands.command(name="guide", aliases=["howto", "tutorial"])
    async def guide(self, ctx: commands.Context):
        """How to use Zero."""
        embed = discord.Embed(title="📖 Zero — Guide", description=GUIDE_TEXT, color=0x1DB954)
        await ctx.send(embed=embed)

    @commands.command(name="premium", aliases=["pro"])
    async def premium(self, ctx: commands.Context):
        """Info about Zero Premium."""
        is_prem = await self.bot.db.is_premium(ctx.guild.id)
        embed = discord.Embed(title="⭐ Zero Premium", description=PREMIUM_INFO, color=0xf1c40f)
        embed.set_footer(text=f"This server: {'✅ Premium' if is_prem else '❌ Not Premium'}")
        await ctx.send(embed=embed)

    @commands.command(name="claim", aliases=["claimvote", "voted"])
    async def claim(self, ctx: commands.Context):
        """Claim 24h premium access after voting on top.gg."""
        # Already has server premium
        if await self.bot.db.is_premium(ctx.guild.id):
            return await ctx.send("✅ This server already has full premium!")

        # Already has an active vote unlock
        if await self.bot.db.has_vote_unlock(ctx.author.id):
            expires = await self.bot.db.vote_unlock_expires(ctx.author.id)
            embed = discord.Embed(
                title="⏳ Already Claimed",
                description=f"You already have an active vote unlock! It expires <t:{expires}:R>.",
                color=0x5865F2
            )
            return await ctx.send(embed=embed)

        # Check top.gg
        msg = await ctx.send("🔎 Checking your vote on top.gg...")
        voted = await check_vote_topgg(ctx.author.id)
        if voted:
            await self.bot.db.add_vote_unlock(ctx.author.id)
            expires = await self.bot.db.vote_unlock_expires(ctx.author.id)
            embed = discord.Embed(
                title="✅ Vote Confirmed!",
                description=(
                    f"Thanks for voting, **{ctx.author.display_name}**! 🎉\n\n"
                    f"You now have **24 hours** of premium access.\n"
                    f"Expires: <t:{expires}:R>\n\n"
                    "Enjoy shuffle, filters, skipto, queue loop & more!"
                ),
                color=0x2ecc71
            )
            await msg.edit(content=None, embed=embed)
        else:
            vote_url = _vote_url()
            embed = discord.Embed(
                title="❌ No Vote Found",
                description=(
                    f"Couldn't find a recent vote from you.\n\n"
                    f"1. [🗳 Vote for Zero on top.gg]({vote_url})\n"
                    f"2. Run `.claim` again after voting\n\n"
                    "Note: top.gg can take up to 1 minute to register your vote."
                ),
                color=0xe74c3c
            )
            await msg.edit(content=None, embed=embed)

    @commands.command(name="votestatus", aliases=["votecheck", "vs"])
    async def votestatus(self, ctx: commands.Context):
        """Check your current vote/premium status."""
        is_server_premium = await self.bot.db.is_premium(ctx.guild.id)
        has_vote          = await self.bot.db.has_vote_unlock(ctx.author.id)
        expires           = await self.bot.db.vote_unlock_expires(ctx.author.id)
        vote_url          = _vote_url()

        embed = discord.Embed(title="⭐ Your Premium Status", color=0xf1c40f)
        embed.add_field(
            name="Server Premium",
            value="✅ Active" if is_server_premium else "❌ Not active",
            inline=True
        )
        embed.add_field(
            name="Vote Unlock",
            value=f"✅ Expires <t:{expires}:R>" if has_vote else "❌ Not active",
            inline=True
        )
        if not is_server_premium and not has_vote:
            embed.add_field(
                name="Get Access",
                value=f"[🗳 Vote on top.gg]({vote_url}) then run `.claim`",
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.command(name="botinfo", aliases=["info", "about"])
    async def botinfo(self, ctx: commands.Context):
        """Info about Zero."""
        embed = discord.Embed(title=f"🤖 {config.BOT_NAME}", color=0x5865F2)
        embed.add_field(name="Servers",  value=str(len(self.bot.guilds)))
        embed.add_field(name="Prefix",   value=f"`{config.PREFIX}`")
        embed.add_field(name="Python",   value=platform.python_version())
        embed.add_field(name="discord.py", value=discord.__version__)
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        await ctx.send(embed=embed)

    # ── PREMIUM ADMIN (owner only) ────────────────────────────────────────────
    @commands.command(name="premium_add", aliases=["addpremium"])
    @commands.is_owner()
    async def premium_add(self, ctx: commands.Context, guild_id: int):
        """[Owner] Grant premium to a guild."""
        await self.bot.db.add_premium(guild_id, ctx.author.id)
        await ctx.send(f"✅ Premium granted to guild `{guild_id}`.")

    @commands.command(name="premium_remove", aliases=["removepremium"])
    @commands.is_owner()
    async def premium_remove(self, ctx: commands.Context, guild_id: int):
        """[Owner] Revoke premium from a guild."""
        await self.bot.db.remove_premium(guild_id)
        await ctx.send(f"✅ Premium revoked for guild `{guild_id}`.")

    @commands.command(name="premium_list", aliases=["listpremium"])
    @commands.is_owner()
    async def premium_list(self, ctx: commands.Context):
        """[Owner] List all premium guilds."""
        lst = await self.bot.db.list_premium()
        if not lst:
            return await ctx.send("No premium guilds.")
        await ctx.send("⭐ Premium guilds:\n" + "\n".join(f"`{g}`" for g in lst))


async def setup(bot):
    await bot.add_cog(Utility(bot))
