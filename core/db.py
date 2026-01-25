# core/db.py
import aiosqlite
import asyncio
import time
import os
import typing
import config

DB_PATH = os.getenv("DB_PATH", config.DB_PATH)

CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS liked_songs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    track_uri TEXT NOT NULL,
    title TEXT,
    author TEXT,
    length INTEGER,
    added_at INTEGER
);

CREATE TABLE IF NOT EXISTS premium_guilds (
    guild_id INTEGER PRIMARY KEY,
    granted_at INTEGER
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
    def __init__(self, path: str = DB_PATH):
        self.path = path
        # single connection approach often fine; using connect per-op for reliability
        self._lock = asyncio.Lock()

    async def init(self):
        async with aiosqlite.connect(self.path) as db:
            await db.executescript(CREATE_TABLES)
            await db.commit()

    # ---------- liked songs ----------
    async def add_liked(self, user_id: int, track_uri: str, title: str, author: str, length: int):
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT INTO liked_songs (user_id, track_uri, title, author, length, added_at) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, track_uri, title, author, length, int(time.time()))
            )
            await db.commit()

    async def get_liked(self, user_id: int, limit: int = 100):
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute("SELECT id, track_uri, title, author, length, added_at FROM liked_songs WHERE user_id = ? ORDER BY added_at DESC LIMIT ?", (user_id, limit))
            rows = await cur.fetchall()
            return rows

    async def remove_liked(self, user_id: int, liked_id: int):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("DELETE FROM liked_songs WHERE user_id = ? AND id = ?", (user_id, liked_id))
            await db.commit()

    async def clear_liked(self, user_id: int):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("DELETE FROM liked_songs WHERE user_id = ?", (user_id,))
            await db.commit()

    # ---------- premium ----------
    async def grant_guild_premium(self, guild_id: int):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("INSERT OR REPLACE INTO premium_guilds (guild_id, granted_at) VALUES (?, ?)", (guild_id, int(time.time())))
            await db.commit()

    async def revoke_guild_premium(self, guild_id: int):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("DELETE FROM premium_guilds WHERE guild_id = ?", (guild_id,))
            await db.commit()

    async def is_guild_premium(self, guild_id: int) -> bool:
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute("SELECT 1 FROM premium_guilds WHERE guild_id = ?", (guild_id,))
            row = await cur.fetchone()
            return row is not None

    # ---------- playlists ----------
    async def create_playlist(self, user_id: int, name: str):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("INSERT INTO playlists (user_id, name) VALUES (?, ?)", (user_id, name))
            await db.commit()

    async def add_playlist_track(self, playlist_id: int, title: str, url: str):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("INSERT INTO playlist_tracks (playlist_id, title, url) VALUES (?, ?, ?)", (playlist_id, title, url))
            await db.commit()
