# core/db.py
import aiosqlite
import asyncio
import time
from typing import List, Optional, Tuple
import config

CREATE_TABLES_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS premium_guilds (
    guild_id INTEGER PRIMARY KEY,
    activated_by INTEGER,
    activated_at INTEGER
);

CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id INTEGER PRIMARY KEY,
    mode_247 INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS liked_songs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    track_uri TEXT NOT NULL,
    title TEXT,
    author TEXT,
    length INTEGER,
    added_at INTEGER
);

CREATE TABLE IF NOT EXISTS playlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT
);

CREATE TABLE IF NOT EXISTS playlist_tracks (
    playlist_id INTEGER,
    title TEXT,
    url TEXT
);
"""


class Database:
    def __init__(self, path: str = None):
        self.path = path or getattr(config, "DB_PATH", "database.db")
        self._lock = asyncio.Lock()
        self._conn: Optional[aiosqlite.Connection] = None

    async def init(self):
        self._conn = await aiosqlite.connect(self.path)
        await self._conn.executescript(CREATE_TABLES_SQL)
        await self._conn.commit()

    # ── PREMIUM ───────────────────────────────────────────────────────────────

    async def add_premium_guild(self, guild_id: int, activated_by: int = None):
        async with self._lock:
            now = int(time.time())
            await self._conn.execute(
                "INSERT OR REPLACE INTO premium_guilds (guild_id, activated_by, activated_at) VALUES (?, ?, ?)",
                (guild_id, activated_by or 0, now)
            )
            await self._conn.commit()

    async def remove_premium_guild(self, guild_id: int):
        async with self._lock:
            await self._conn.execute("DELETE FROM premium_guilds WHERE guild_id = ?", (guild_id,))
            await self._conn.commit()

    async def is_premium_guild(self, guild_id: int) -> bool:
        async with self._lock:
            cur = await self._conn.execute("SELECT 1 FROM premium_guilds WHERE guild_id = ?", (guild_id,))
            row = await cur.fetchone()
            return row is not None

    async def list_premium_guilds(self) -> List[int]:
        async with self._lock:
            cur = await self._conn.execute("SELECT guild_id FROM premium_guilds")
            rows = await cur.fetchall()
            return [r[0] for r in rows]

    # ── 24/7 MODE ─────────────────────────────────────────────────────────────

    async def is_247(self, guild_id: int) -> bool:
        async with self._lock:
            cur = await self._conn.execute(
                "SELECT mode_247 FROM guild_settings WHERE guild_id = ?", (guild_id,)
            )
            row = await cur.fetchone()
            return bool(row and row[0])

    async def set_247(self, guild_id: int, enabled: bool):
        async with self._lock:
            await self._conn.execute(
                "INSERT INTO guild_settings (guild_id, mode_247) VALUES (?, ?) "
                "ON CONFLICT(guild_id) DO UPDATE SET mode_247 = excluded.mode_247",
                (guild_id, int(enabled))
            )
            await self._conn.commit()

    # ── LIKED SONGS ───────────────────────────────────────────────────────────

    async def add_liked(self, user_id: int, track_uri: str, title: str, author: str, length: int):
        async with self._lock:
            now = int(time.time())
            await self._conn.execute(
                "INSERT INTO liked_songs (user_id, track_uri, title, author, length, added_at) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, track_uri, title, author, length, now)
            )
            await self._conn.commit()

    async def get_liked(self, user_id: int, limit: int = 100):
        async with self._lock:
            cur = await self._conn.execute(
                "SELECT id, track_uri, title, author, length, added_at FROM liked_songs "
                "WHERE user_id = ? ORDER BY added_at DESC LIMIT ?",
                (user_id, limit)
            )
            return await cur.fetchall()

    async def remove_liked(self, user_id: int, liked_id: int):
        async with self._lock:
            await self._conn.execute("DELETE FROM liked_songs WHERE user_id = ? AND id = ?", (user_id, liked_id))
            await self._conn.commit()

    async def clear_liked(self, user_id: int):
        async with self._lock:
            await self._conn.execute("DELETE FROM liked_songs WHERE user_id = ?", (user_id,))
            await self._conn.commit()

    # ── PLAYLISTS ─────────────────────────────────────────────────────────────

    async def create_playlist(self, user_id: int, name: str):
        async with self._lock:
            await self._conn.execute("INSERT INTO playlists (user_id, name) VALUES (?, ?)", (user_id, name))
            await self._conn.commit()

    async def add_track(self, user_id: int, playlist: str, title: str, url: str) -> bool:
        async with self._lock:
            cur = await self._conn.execute(
                "SELECT id FROM playlists WHERE user_id=? AND name=?", (user_id, playlist)
            )
            pid = await cur.fetchone()
            if not pid:
                return False
            await self._conn.execute(
                "INSERT INTO playlist_tracks VALUES (?, ?, ?)", (pid[0], title, url)
            )
            await self._conn.commit()
            return True

    async def get_playlist(self, user_id: int, name: str) -> List[Tuple[str, str]]:
        async with self._lock:
            cur = await self._conn.execute("""
            SELECT title, url FROM playlist_tracks
            WHERE playlist_id = (
                SELECT id FROM playlists WHERE user_id=? AND name=?
            )
            """, (user_id, name))
            return await cur.fetchall()

    async def list_playlists(self, user_id: int) -> List[Tuple[str, int]]:
        """Returns list of (name, track_count) tuples."""
        async with self._lock:
            cur = await self._conn.execute("""
            SELECT p.name, COUNT(pt.playlist_id) as cnt
            FROM playlists p
            LEFT JOIN playlist_tracks pt ON pt.playlist_id = p.id
            WHERE p.user_id = ?
            GROUP BY p.id, p.name
            ORDER BY p.id
            """, (user_id,))
            return await cur.fetchall()

    async def delete_playlist(self, user_id: int, name: str) -> bool:
        async with self._lock:
            cur = await self._conn.execute(
                "SELECT id FROM playlists WHERE user_id=? AND name=?", (user_id, name)
            )
            pid = await cur.fetchone()
            if not pid:
                return False
            await self._conn.execute("DELETE FROM playlist_tracks WHERE playlist_id=?", (pid[0],))
            await self._conn.execute("DELETE FROM playlists WHERE id=?", (pid[0],))
            await self._conn.commit()
            return True
