# core/db.py
import aiosqlite
import asyncio
import time
import config

CREATE = """
CREATE TABLE IF NOT EXISTS liked_songs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    track_uri TEXT NOT NULL,
    title TEXT,
    author TEXT,
    length INTEGER,
    added_at INTEGER
);

CREATE TABLE IF NOT EXISTS premium_users (
    user_id INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS guild_247 (
    guild_id INTEGER PRIMARY KEY,
    enabled INTEGER
);

CREATE TABLE IF NOT EXISTS playlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT
);

CREATE TABLE IF NOT EXISTS playlist_tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    playlist_id INTEGER,
    title TEXT,
    url TEXT
);
"""

class Database:
    def __init__(self, path: str = config.DB_PATH):
        self.path = path
        self._lock = asyncio.Lock()

    async def init(self):
        async with aiosqlite.connect(self.path) as db:
            await db.executescript(CREATE)
            await db.commit()

    # Liked songs
    async def add_liked(self, user_id: int, track_uri: str, title: str, author: str, length: int):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("INSERT INTO liked_songs (user_id, track_uri, title, author, length, added_at) VALUES (?, ?, ?, ?, ?, ?)",
                             (user_id, track_uri, title, author, length, int(time.time())))
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

    # Premium
    async def is_premium_user(self, user_id: int):
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute("SELECT 1 FROM premium_users WHERE user_id = ?", (user_id,))
            return await cur.fetchone() is not None

    async def set_247(self, guild_id: int, enabled: bool):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("INSERT OR REPLACE INTO guild_247 (guild_id, enabled) VALUES (?, ?)", (guild_id, int(enabled)))
            await db.commit()

    async def is_247(self, guild_id: int):
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute("SELECT enabled FROM guild_247 WHERE guild_id = ?", (guild_id,))
            row = await cur.fetchone()
            return row and row[0] == 1

    # Playlists
    async def create_playlist(self, user_id: int, name: str):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("INSERT INTO playlists (user_id, name) VALUES (?, ?)", (user_id, name))
            await db.commit()

    async def add_track_to_playlist(self, user_id: int, playlist_name: str, title: str, url: str):
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute("SELECT id FROM playlists WHERE user_id = ? AND name = ?", (user_id, playlist_name))
            pid = await cur.fetchone()
            if not pid:
                return False
            await db.execute("INSERT INTO playlist_tracks (playlist_id, title, url) VALUES (?, ?, ?)", (pid[0], title, url))
            await db.commit()
            return True

    async def get_playlist_tracks(self, user_id: int, playlist_name: str):
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute("""
                SELECT title, url FROM playlist_tracks
                WHERE playlist_id = (
                    SELECT id FROM playlists WHERE user_id = ? AND name = ?
                )
            """, (user_id, playlist_name))
            return await cur.fetchall()
