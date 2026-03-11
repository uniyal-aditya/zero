# core/ytdl.py
import asyncio, logging
from concurrent.futures import ThreadPoolExecutor
import yt_dlp

log = logging.getLogger("zero")
_executor = ThreadPoolExecutor(max_workers=4)

YTDL_OPTS = {
    "format": "bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch5",
    "skip_download": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "source_address": "0.0.0.0",
    "extract_flat": False,
}

def _run_sync(query: str, flat=False) -> dict | None:
    opts = dict(YTDL_OPTS)
    if flat:
        opts["extract_flat"] = True
    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            return ydl.extract_info(query, download=False)
        except Exception as e:
            log.error("yt_dlp error: %s", e)
            return None

async def _run(query: str, flat=False) -> dict | None:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, lambda: _run_sync(query, flat))

async def fetch_track(query: str) -> dict | None:
    """Fetch a single track. Returns dict with url, title, webpage_url, duration, thumbnail."""
    info = await _run(query)
    if not info:
        return None
    if "entries" in info:
        entries = [e for e in info["entries"] if e]
        if not entries:
            return None
        info = entries[0]
        # Flat entry — need full info
        if "url" not in info or not info["url"].startswith("http"):
            info = await _run(info.get("webpage_url") or info.get("url") or query)
            if not info:
                return None
    return {
        "url":         info.get("url", ""),
        "title":       info.get("title", "Unknown"),
        "webpage_url": info.get("webpage_url", query),
        "duration":    info.get("duration") or 0,
        "thumbnail":   info.get("thumbnail", ""),
    }

async def search_tracks(query: str, limit: int = 5) -> list[dict]:
    """Search YouTube and return up to `limit` results."""
    info = await _run(f"ytsearch{limit}:{query}")
    if not info or "entries" not in info:
        return []
    results = []
    for e in info["entries"]:
        if not e:
            continue
        results.append({
            "url":         e.get("url", ""),
            "title":       e.get("title", "Unknown"),
            "webpage_url": e.get("webpage_url", ""),
            "duration":    e.get("duration") or 0,
            "thumbnail":   e.get("thumbnail", ""),
        })
    return results[:limit]
