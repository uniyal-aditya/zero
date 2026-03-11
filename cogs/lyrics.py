# cogs/lyrics.py
import os, logging, aiohttp
import discord
from discord.ext import commands

log = logging.getLogger("zero")

class Lyrics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="lyrics", aliases=["ly"])
    async def lyrics(self, ctx: commands.Context, *, query: str = None):
        """Get lyrics for the current or searched song."""
        if not query:
            cog = self.bot.get_cog("Music")
            player = cog.get_player(ctx.guild) if cog else None
            if not player or not player.current:
                return await ctx.send("❌ Provide a song name or play something first.")
            query = player.current.title

        await ctx.typing()
        # Use lyrics.ovh — free, no API key needed
        clean = query.split("(")[0].split("[")[0].strip()
        # Try to split into artist/title if possible
        parts = clean.split("-", 1)
        if len(parts) == 2:
            artist, title = parts[0].strip(), parts[1].strip()
        else:
            artist, title = "any", clean

        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.lyrics.ovh/v1/{artist}/{title}"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status != 200:
                        # fallback: try reversed
                        url2 = f"https://api.lyrics.ovh/v1/{title}/{artist}"
                        async with session.get(url2, timeout=aiohttp.ClientTimeout(total=10)) as resp2:
                            if resp2.status != 200:
                                return await ctx.send(f"❌ No lyrics found for **{query}**.")
                            data = await resp2.json()
                    else:
                        data = await resp.json()

            text = data.get("lyrics", "")
            if not text:
                return await ctx.send(f"❌ No lyrics found for **{query}**.")

            # Paginate — discord limit 4096 per embed
            chunks = [text[i:i+3900] for i in range(0, min(len(text), 12000), 3900)]
            for idx, chunk in enumerate(chunks):
                embed = discord.Embed(
                    title=f"🎤 {query}" if idx == 0 else f"🎤 {query} (cont.)",
                    description=chunk,
                    color=0x1DB954
                )
                if idx == 0:
                    embed.set_footer(text="Lyrics provided by lyrics.ovh")
                await ctx.send(embed=embed)

        except Exception as e:
            log.error("Lyrics error: %s", e)
            await ctx.send("❌ Failed to fetch lyrics. Try again later.")


async def setup(bot):
    await bot.add_cog(Lyrics(bot))
