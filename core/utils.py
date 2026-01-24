# core/utils.py
import re
from urllib.parse import urlparse, parse_qs

YOUTUBE_RE = re.compile(r"(?:youtube\.com|youtu\.be)")
SPOTIFY_RE = re.compile(r"open\.spotify\.com|spotify:")

def is_youtube_url(text: str) -> bool:
    if not text:
        return False
    return bool(YOUTUBE_RE.search(text))

def is_spotify_url(text: str) -> bool:
    if not text:
        return False
    return bool(SPOTIFY_RE.search(text))

def extract_spotify_id(url: str) -> str | None:
    # supports open.spotify.com/track/<id> or spotify:track:<id>
    if "open.spotify.com" in url:
        parts = url.split("/")
        if len(parts) >= 5:
            return parts[4].split("?")[0]
    if url.startswith("spotify:"):
        return url.split(":")[-1]
    return None
