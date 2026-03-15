import json
import os
import time
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

FILES = ["premium", "votes", "playlists", "liked_songs", "settings"]
for f in FILES:
    fp = DATA_DIR / f"{f}.json"
    if not fp.exists():
        fp.write_text("{}")


def _read(name: str) -> dict:
    try:
        return json.loads((DATA_DIR / f"{name}.json").read_text())
    except Exception:
        return {}


def _write(name: str, data: dict):
    (DATA_DIR / f"{name}.json").write_text(json.dumps(data, indent=2))


# ── PREMIUM (server-level, owner-granted) ─────────────────────────────────────

def is_premium_guild(guild_id: int) -> bool:
    return _read("premium").get(str(guild_id), {}).get("active", False)


def grant_premium(guild_id: int, granted_by: int):
    d = _read("premium")
    d[str(guild_id)] = {"active": True, "granted_by": granted_by, "granted_at": int(time.time())}
    _write("premium", d)


def revoke_premium(guild_id: int):
    d = _read("premium")
    if str(guild_id) in d:
        d[str(guild_id)]["active"] = False
        d[str(guild_id)]["revoked_at"] = int(time.time())
    _write("premium", d)


def get_premium_info(guild_id: int) -> dict | None:
    return _read("premium").get(str(guild_id))


def all_premium_guilds() -> list[str]:
    return [k for k, v in _read("premium").items() if v.get("active")]


# ── VOTE PREMIUM (user-level, 12 hrs) ─────────────────────────────────────────

def grant_vote_premium(user_id: int, hours: int = 12):
    d = _read("votes")
    d[str(user_id)] = {"expires_at": int(time.time()) + hours * 3600, "voted_at": int(time.time())}
    _write("votes", d)


def has_vote_premium(user_id: int) -> bool:
    entry = _read("votes").get(str(user_id))
    return bool(entry and entry["expires_at"] > time.time())


def vote_expiry(user_id: int) -> int | None:
    entry = _read("votes").get(str(user_id))
    return entry["expires_at"] if entry else None


# ── ACCESS CHECK ──────────────────────────────────────────────────────────────

def has_access(guild_id: int, user_id: int) -> bool:
    return is_premium_guild(guild_id) or has_vote_premium(user_id)


# ── PLAYLISTS ─────────────────────────────────────────────────────────────────

def get_playlists(user_id: int) -> dict:
    return _read("playlists").get(str(user_id), {})


def get_playlist(user_id: int, name: str) -> dict | None:
    return get_playlists(user_id).get(name.lower())


def create_playlist(user_id: int, name: str) -> bool:
    d = _read("playlists")
    uid = str(user_id)
    if uid not in d:
        d[uid] = {}
    key = name.lower()
    if key in d[uid]:
        return False
    d[uid][key] = {"name": name, "songs": [], "created_at": int(time.time())}
    _write("playlists", d)
    return True


def delete_playlist(user_id: int, name: str) -> bool:
    d = _read("playlists")
    uid = str(user_id)
    key = name.lower()
    if uid not in d or key not in d[uid]:
        return False
    del d[uid][key]
    _write("playlists", d)
    return True


def add_song_to_playlist(user_id: int, name: str, song: dict) -> bool:
    d = _read("playlists")
    uid = str(user_id)
    key = name.lower()
    if uid not in d or key not in d[uid]:
        return False
    d[uid][key]["songs"].append({**song, "added_at": int(time.time())})
    _write("playlists", d)
    return True


def remove_song_from_playlist(user_id: int, name: str, index: int) -> bool:
    d = _read("playlists")
    uid = str(user_id)
    key = name.lower()
    songs = d.get(uid, {}).get(key, {}).get("songs", [])
    if not songs or index < 0 or index >= len(songs):
        return False
    songs.pop(index)
    _write("playlists", d)
    return True


def rename_playlist(user_id: int, old: str, new: str):
    """Returns True, False (not found), or 'exists'."""
    d = _read("playlists")
    uid = str(user_id)
    ok, nk = old.lower(), new.lower()
    if uid not in d or ok not in d[uid]:
        return False
    if nk in d[uid]:
        return "exists"
    d[uid][nk] = {**d[uid][ok], "name": new}
    del d[uid][ok]
    _write("playlists", d)
    return True


# ── LIKED SONGS ───────────────────────────────────────────────────────────────

def get_liked_songs(user_id: int) -> list:
    return _read("liked_songs").get(str(user_id), [])


def like_song(user_id: int, song: dict) -> bool:
    d = _read("liked_songs")
    uid = str(user_id)
    if uid not in d:
        d[uid] = []
    if any(s["url"] == song["url"] for s in d[uid]):
        return False
    d[uid].insert(0, {**song, "liked_at": int(time.time())})
    _write("liked_songs", d)
    return True


def unlike_song(user_id: int, url: str) -> bool:
    d = _read("liked_songs")
    uid = str(user_id)
    if uid not in d:
        return False
    before = len(d[uid])
    d[uid] = [s for s in d[uid] if s["url"] != url]
    if len(d[uid]) == before:
        return False
    _write("liked_songs", d)
    return True


def is_liked(user_id: int, url: str) -> bool:
    return any(s["url"] == url for s in get_liked_songs(user_id))


# ── SETTINGS ──────────────────────────────────────────────────────────────────

def get_settings(guild_id: int) -> dict:
    return _read("settings").get(str(guild_id), {"dj_role": None, "tf_seven": False, "default_volume": 80})


def set_setting(guild_id: int, key: str, value):
    d = _read("settings")
    uid = str(guild_id)
    if uid not in d:
        d[uid] = {}
    d[uid][key] = value
    _write("settings", d)
