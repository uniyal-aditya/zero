import discord
from discord.ext import commands
import config as cfg
import utils.database as db


def is_owner():
    async def predicate(ctx):
        if ctx.author.id != cfg.OWNER_ID:
            raise commands.CheckFailure("This command is restricted to the bot owner.")
        return True
    return commands.check(predicate)


def in_voice():
    async def predicate(ctx):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CheckFailure("You must be in a voice channel!")
        return True
    return commands.check(predicate)


def same_voice():
    async def predicate(ctx):
        player = ctx.guild.voice_client
        if player and ctx.author.voice and ctx.author.voice.channel != player.channel:
            raise commands.CheckFailure("You must be in the **same** voice channel as me!")
        return True
    return commands.check(predicate)


def bot_in_voice():
    async def predicate(ctx):
        if not ctx.guild.voice_client:
            raise commands.CheckFailure("I'm not in a voice channel right now.")
        return True
    return commands.check(predicate)


def is_dj():
    async def predicate(ctx):
        if ctx.author.id == cfg.OWNER_ID:
            return True
        if ctx.author.guild_permissions.manage_guild:
            return True
        settings = db.get_settings(ctx.guild.id)
        dj_role_id = settings.get("dj_role")
        if dj_role_id:
            role = ctx.guild.get_role(int(dj_role_id))
            if role and role in ctx.author.roles:
                return True
            raise commands.CheckFailure("You need the DJ role to use this command.")
        return True  # no dj role set = everyone can use
    return commands.check(predicate)


def premium_required():
    async def predicate(ctx):
        if not db.has_access(ctx.guild.id, ctx.author.id):
            raise commands.CheckFailure("PREMIUM_REQUIRED")
        return True
    return commands.check(predicate)


async def handle_check_error(ctx, error):
    """Call from cog error handlers to handle check failures cleanly."""
    from utils.embeds import err, premium_wall
    if isinstance(error, commands.CheckFailure):
        if str(error) == "PREMIUM_REQUIRED":
            await ctx.reply(embed=premium_wall(), mention_author=False)
        else:
            await ctx.reply(embed=err(str(error)), mention_author=False)
        return True
    return False
