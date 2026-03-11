# core/checks.py
import os, discord
from discord.ext import commands
from discord import ui
from core.votes import check_vote_topgg, _vote_url

class PremiumGateView(discord.ui.View):
    def __init__(self, vote_url: str, allow_vote: bool = True):
        super().__init__(timeout=None)
        if allow_vote:
            self.add_item(discord.ui.Button(
                label="Vote",
                emoji="🗳️",
                style=discord.ButtonStyle.primary,
                url=vote_url,
            ))
        self.add_item(discord.ui.Button(
            label="Premium",
            emoji="⭐",
            style=discord.ButtonStyle.secondary,
            url="https://discord.gg/",   # replace with your support server or premium info link
        ))


def _gate_embed(allow_vote: bool = True, expires_ts: int = 0, voted: bool = False) -> discord.Embed:
    import config

    # ── Success after vote ────────────────────────────────────────────────────
    if voted:
        embed = discord.Embed(
            description="✅ **Vote confirmed!** You now have **24h** of premium access.\nExpires <t:{}>:R>.".format(expires_ts),
            color=0x2ecc71
        )
        return embed

    # ── 247 gate (vote not allowed) ───────────────────────────────────────────
    if not allow_vote:
        embed = discord.Embed(
            description=(
                "**Premium Required**\n"
                "You need **server premium** to use 24/7 mode.\n"
                "Use `{}premium` for more info.".format(config.PREFIX)
            ),
            color=0x5865F2
        )
        embed.set_author(name="Zero", icon_url=None)
        return embed

    # ── Standard vote gate ────────────────────────────────────────────────────
    embed = discord.Embed(
        description=(
            "**Vote Required!**\n"
            "You need to vote me on **topgg** in order to use this feature "
            "else bypass by **premium**"
        ),
        color=0x5865F2
    )
    embed.set_author(name="Zero")
    return embed


async def premium_or_vote(
    ctx: commands.Context,
    allow_vote: bool = True
) -> bool:
    bot = ctx.bot
    vote_url = _vote_url()

    # 1. Guild has full premium
    if await bot.db.is_premium(ctx.guild.id):
        return True

    # 2. 247 — never unlockable via vote
    if not allow_vote:
        await ctx.send(
            embed=_gate_embed(allow_vote=False),
            view=PremiumGateView(vote_url, allow_vote=False)
        )
        return False

    # 3. User has an active vote unlock in DB
    if await bot.db.has_vote_unlock(ctx.author.id):
        return True

    # 4. Check top.gg live — user may have voted without claiming
    voted = await check_vote_topgg(ctx.author.id)
    if voted:
        await bot.db.add_vote_unlock(ctx.author.id)
        expires = await bot.db.vote_unlock_expires(ctx.author.id)
        await ctx.send(embed=_gate_embed(voted=True, expires_ts=expires))
        return True

    # 5. Blocked — show Lara-style gate with buttons
    bot_icon = ctx.bot.user.display_avatar.url if ctx.bot.user else None
    embed = _gate_embed(allow_vote=True)
    embed.set_author(name="Zero", icon_url=bot_icon)
    await ctx.send(embed=embed, view=PremiumGateView(vote_url, allow_vote=True))
    return False
