# core/utils.py
import re
from urllib.parse import urlparse

SPOTIFY_TRACK_RE = re.compile(r"(?:https?://)?(?:open\.)?spotify\.com/track/([A-Za-z0-9]+)")
SPOTIFY_PLAYLIST_RE = re.compile(r"(?:https?://)?(?:open\.)?spotify\.com/playlist/([A-Za-z0-9]+)")
SPOTIFY_ALBUM_RE = re.compile(r"(?:https?://)?(?:open\.)?spotify\.com/album/([A-Za-z0-9]+)")

def is_youtube_url(query: str) -> bool:
    parsed = urlparse(query)
    return parsed.netloc and ("youtube" in parsed.netloc or "youtu.be" in parsed.netloc)

def is_spotify_url(query: str) -> bool:
    return "spotify.com" in query

def extract_spotify_id(query: str):
    m = SPOTIFY_TRACK_RE.search(query)
    if m:
        return ("track", m.group(1))
    m = SPOTIFY_PLAYLIST_RE.search(query)
    if m:
        return ("playlist", m.group(1))
    m = SPOTIFY_ALBUM_RE.search(query)
    if m:
        return ("album", m.group(1))
    return (None, None)
