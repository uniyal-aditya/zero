# core/votes.py
import os, logging, aiohttp

log = logging.getLogger("zero")

TOPGG_TOKEN    = os.getenv("TOPGG_TOKEN", "")
BOT_ID         = os.getenv("APPLICATION_ID", "")
TOPGG_BOT_SLUG = os.getenv("TOPGG_BOT_SLUG", "")

def _vote_url() -> str:
    if TOPGG_BOT_SLUG:
        return f"https://top.gg/bot/{TOPGG_BOT_SLUG}/vote"
    if BOT_ID:
        return f"https://top.gg/bot/{BOT_ID}/vote"
    return "https://top.gg"

async def check_vote_topgg(user_id: int) -> bool:
    """
    Returns True if the user has voted for the bot on top.gg in the last 12h.
    Requires TOPGG_TOKEN env var.
    """
    if not TOPGG_TOKEN or not BOT_ID:
        return False
    url = f"https://top.gg/api/bots/{BOT_ID}/check?userId={user_id}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers={"Authorization": TOPGG_TOKEN},
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                if resp.status != 200:
                    log.warning("top.gg vote check returned %d", resp.status)
                    return False
                data = await resp.json()
                return bool(data.get("voted", 0))
    except Exception as e:
        log.error("top.gg vote check error: %s", e)
        return False
