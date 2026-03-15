import aiohttp
import config as cfg


async def has_voted(user_id: int) -> bool:
    """Check if a user has voted on Top.gg within the last 12 hours."""
    if not cfg.TOPGG_TOKEN or not cfg.TOPGG_BOT_ID:
        return False
    url = f"https://top.gg/api/bots/{cfg.TOPGG_BOT_ID}/check?userId={user_id}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={"Authorization": cfg.TOPGG_TOKEN}, timeout=aiohttp.ClientTimeout(total=5)) as r:
                if r.status == 200:
                    data = await r.json()
                    return data.get("voted") == 1
    except Exception:
        pass
    return False
