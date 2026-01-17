# core/db.py
import aiosqlite
import asyncio
import time
import config

CREATE_TABLES = """
-- Liked songs
CREATE TABLE IF NOT EXISTS liked_songs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    track_uri TEXT NOT NULL,
    title TEXT,
    author TEXT,
    length INTEGER,
    added_at INTEGER
);
CREATE INDEX IF NOT EXISTS idx_liked_user ON liked_songs (user_id);

-- Premium users
CREATE TABLE IF NOT EXISTS premium_users (
    user_id INTEGER PRIMARY KEY
);

-- 24/7 guild mode
CREATE TABLE IF NOT EXISTS guild_247 (
    guild_id INTEGER PRIMARY KEY,
    enabled INTEGER
);

-- Playlists
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
    def __init__(self, path=config.DB_PATH):
        self.path = path
        self._conn: aiosqlite.Connection | None = None
        self._lock = asyncio.Lock()

    async def init(self):
        self._conn = await aiosqlite.connect(self.path)
        await self._conn.executescript(CREATE_TABLES)
        await self._conn.commit()

    # =========================
    # ❤️ LIKED SONGS
    # =========================
    async def add_liked(self, user_id, track_uri, title, author, length):
        async with self._lock:
            await self._conn.execute(
                """INSERT INTO liked_songs
                (user_id, track_uri, title, author, length, added_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, track_uri, title, author, length, int(time.time()))
            )
            await self._conn.commit()

    async def get_liked(self, user_id, limit=100):
        async with self._lock:
            cur = await self._conn.execute(
                """SELECT id, track_uri, title, author, length, added_at
                   FROM liked_songs
                   WHERE user_id=?
                   ORDER BY added_at DESC
                   LIMIT ?""",
                (user_id, limit)
            )
            return await cur.fetchall()

    async def remove_liked(self, user_id, liked_id):
        async with self._lock:
            await self._conn.execute(
                "DELETE FROM liked_songs WHERE user_id=? AND id=?",
                (user_id, liked_id)
            )
            await self._conn.commit()

    async def clear_liked(self, user_id):
        async with self._lock:
            await self._conn.execute(
                "DELETE FROM liked_songs WHERE user_id=?",
                (user_id,)
            )
            await self._conn.commit()

    async def count_liked(self, user_id):
        async with self._lock:
            cur = await self._conn.execute(
                "SELECT COUNT(*) FROM liked_songs WHERE user_id=?",
                (user_id,)
            )
            row = await cur.fetchone()
            return row[0] if row else 0

    async def export_liked(self, user_id):
        rows = await self.get_liked(user_id, limit=10000)
        return [
            {
                "id": r[0],
                "track_uri": r[1],
                "title": r[2],
                "author": r[3],
                "length": r[4],
                "added_at": r[5],
            }
            for r in rows
        ]

    async def import_liked(self, user_id, items):
        async with self._lock:
            for it in items:
                await self._conn.execute(
                    """INSERT INTO liked_songs
                    (user_id, track_uri, title, author, length, added_at)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        user_id,
                        it.get("track_uri"),
                        it.get("title"),
                        it.get("author"),
                        it.get("length", 0),
                        int(it.get("added_at", time.time()))
                    )
                )
            await self._conn.commit()

    # =========================
    # 💎 PREMIUM
    # =========================
    async def is_premium_user(self, user_id):
        async with self._lock:
            cur = await self._conn.execute(
                "SELECT 1 FROM premium_users WHERE user_id=?",
                (user_id,)
            )
            return await cur.fetchone() is not None

    async def add_premium_user(self, user_id):
        async with self._lock:
            await self._conn.execute(
                "INSERT OR IGNORE INTO premium_users VALUES (?)",
                (user_id,)
            )
            await self._conn.commit()

    # =========================
    # 🔒 24/7 MODE
    # =========================
    async def set_247(self, guild_id, enabled: bool):
        async with self._lock:
            await self._conn.execute(
                "INSERT OR REPLACE INTO guild_247 VALUES (?, ?)",
                (guild_id, int(enabled))
            )
            await self._conn.commit()

    async def is_247(self, guild_id):
        async with self._lock:
            cur = await self._conn.execute(
                "SELECT enabled FROM guild_247 WHERE guild_id=?",
                (guild_id,)
            )
            row = await cur.fetchone()
            return bool(row and row[0] == 1)

    # =========================
    # 🎶 PLAYLISTS
    # =========================
    async def create_playlist(self, user_id, name):
        async with self._lock:
            await self._conn.execute(
                "INSERT INTO playlists (user_id, name) VALUES (?, ?)",
                (user_id, name)
            )
            await self._conn.commit()

    async def add_track_to_playlist(self, user_id, playlist_name, title, url):
        async with self._lock:
            cur = await self._conn.execute(
                "SELECT id FROM playlists WHERE user_id=? AND name=?",
                (user_id, playlist_name)
            )
            row = await cur.fetchone()
            if not row:
                return False

            await self._conn.execute(
                "INSERT INTO playlist_tracks VALUES (?, ?, ?)",
                (row[0], title, url)
            )
            await self._conn.commit()
            return True

    async def get_playlist(self, user_id, name):
        async with self._lock:
            cur = await self._conn.execute(
                """SELECT title, url FROM playlist_tracks
                   WHERE playlist_id = (
                       SELECT id FROM playlists
                       WHERE user_id=? AND name=?
                   )""",
                (user_id, name)
            )
            return await cur.fetchall()
