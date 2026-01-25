# core/utils.py
import re

YOUTUBE_REGEX = re.compile(r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/")
SPOTIFY_REGEX = re.compile(r"(https?://)?(open\.)?spotify\.com/")

def is_youtube_url(url: str) -> bool:
    return bool(YOUTUBE_REGEX.search(url or ""))

def is_spotify_url(url: str) -> bool:
    return bool(SPOTIFY_REGEX.search(url or ""))
