# core/db.py
import aiosqlite, asyncio, time
from typing import Optional, List, Tuple

SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS premium_guilds (
    guild_id     INTEGER PRIMARY KEY,
    activated_by INTEGER,
    activated_at INTEGER
);
CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id     INTEGER PRIMARY KEY,
    mode_247     INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS liked_songs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL,
    track_url    TEXT NOT NULL,
    title        TEXT,
    added_at     INTEGER
);
CREATE TABLE IF NOT EXISTS playlists (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL,
    name         TEXT NOT NULL,
    UNIQUE(user_id, name)
);
CREATE TABLE IF NOT EXISTS playlist_tracks (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    playlist_id  INTEGER NOT NULL,
    title        TEXT,
    url          TEXT,
    position     INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS vote_unlocks (
    user_id      INTEGER PRIMARY KEY,
    unlocked_at  INTEGER NOT NULL,
    expires_at   INTEGER NOT NULL
);
"""

class Database:
    def __init__(self, path: str = "zero.db"):
        self.path = path
        self._lock = asyncio.Lock()
        self._conn: Optional[aiosqlite.Connection] = None

    async def init(self):
        self._conn = await aiosqlite.connect(self.path)
        await self._conn.executescript(SQL)
        await self._conn.commit()

    # ── PREMIUM ──────────────────────────────────────────────────────────────
    async def add_premium(self, guild_id: int, by: int = 0):
        async with self._lock:
            await self._conn.execute(
                "INSERT OR REPLACE INTO premium_guilds VALUES (?,?,?)",
                (guild_id, by, int(time.time())))
            await self._conn.commit()

    async def remove_premium(self, guild_id: int):
        async with self._lock:
            await self._conn.execute("DELETE FROM premium_guilds WHERE guild_id=?", (guild_id,))
            await self._conn.commit()

    async def is_premium(self, guild_id: int) -> bool:
        async with self._lock:
            cur = await self._conn.execute("SELECT 1 FROM premium_guilds WHERE guild_id=?", (guild_id,))
            return await cur.fetchone() is not None

    async def list_premium(self) -> List[int]:
        async with self._lock:
            cur = await self._conn.execute("SELECT guild_id FROM premium_guilds")
            return [r[0] for r in await cur.fetchall()]

    # ── 247 ──────────────────────────────────────────────────────────────────
    async def get_247(self, guild_id: int) -> bool:
        async with self._lock:
            cur = await self._conn.execute("SELECT mode_247 FROM guild_settings WHERE guild_id=?", (guild_id,))
            row = await cur.fetchone()
            return bool(row and row[0])

    async def set_247(self, guild_id: int, val: bool):
        async with self._lock:
            await self._conn.execute(
                "INSERT INTO guild_settings(guild_id,mode_247) VALUES(?,?) "
                "ON CONFLICT(guild_id) DO UPDATE SET mode_247=excluded.mode_247",
                (guild_id, int(val)))
            await self._conn.commit()

    # ── LIKED ─────────────────────────────────────────────────────────────────
    async def add_liked(self, user_id: int, url: str, title: str):
        async with self._lock:
            await self._conn.execute(
                "INSERT INTO liked_songs(user_id,track_url,title,added_at) VALUES(?,?,?,?)",
                (user_id, url, title, int(time.time())))
            await self._conn.commit()

    async def get_liked(self, user_id: int, limit=100) -> List[Tuple]:
        async with self._lock:
            cur = await self._conn.execute(
                "SELECT id,track_url,title FROM liked_songs WHERE user_id=? ORDER BY added_at DESC LIMIT ?",
                (user_id, limit))
            return await cur.fetchall()

    async def remove_liked(self, user_id: int, liked_id: int):
        async with self._lock:
            await self._conn.execute("DELETE FROM liked_songs WHERE user_id=? AND id=?", (user_id, liked_id))
            await self._conn.commit()

    # ── PLAYLISTS ─────────────────────────────────────────────────────────────
    async def pl_create(self, user_id: int, name: str) -> bool:
        try:
            async with self._lock:
                await self._conn.execute("INSERT INTO playlists(user_id,name) VALUES(?,?)", (user_id, name))
                await self._conn.commit()
            return True
        except Exception:
            return False

    async def pl_delete(self, user_id: int, name: str) -> bool:
        async with self._lock:
            cur = await self._conn.execute("SELECT id FROM playlists WHERE user_id=? AND name=?", (user_id, name))
            row = await cur.fetchone()
            if not row:
                return False
            await self._conn.execute("DELETE FROM playlist_tracks WHERE playlist_id=?", (row[0],))
            await self._conn.execute("DELETE FROM playlists WHERE id=?", (row[0],))
            await self._conn.commit()
        return True

    async def pl_add_track(self, user_id: int, name: str, title: str, url: str) -> bool:
        async with self._lock:
            cur = await self._conn.execute("SELECT id FROM playlists WHERE user_id=? AND name=?", (user_id, name))
            row = await cur.fetchone()
            if not row:
                return False
            cur2 = await self._conn.execute("SELECT COUNT(*) FROM playlist_tracks WHERE playlist_id=?", (row[0],))
            cnt = (await cur2.fetchone())[0]
            await self._conn.execute(
                "INSERT INTO playlist_tracks(playlist_id,title,url,position) VALUES(?,?,?,?)",
                (row[0], title, url, cnt))
            await self._conn.commit()
        return True

    async def pl_tracks(self, user_id: int, name: str) -> List[Tuple]:
        async with self._lock:
            cur = await self._conn.execute("""
                SELECT pt.title, pt.url FROM playlist_tracks pt
                JOIN playlists p ON p.id=pt.playlist_id
                WHERE p.user_id=? AND p.name=? ORDER BY pt.position
            """, (user_id, name))
            return await cur.fetchall()

    async def pl_list(self, user_id: int) -> List[Tuple]:
        async with self._lock:
            cur = await self._conn.execute("""
                SELECT p.name, COUNT(pt.id) FROM playlists p
                LEFT JOIN playlist_tracks pt ON pt.playlist_id=p.id
                WHERE p.user_id=? GROUP BY p.id ORDER BY p.id
            """, (user_id,))
            return await cur.fetchall()

    # ── VOTE UNLOCKS ──────────────────────────────────────────────────────────
    async def add_vote_unlock(self, user_id: int):
        """Grant 24hr premium access after a vote."""
        now = int(time.time())
        expires = now + 86400  # 24 hours
        async with self._lock:
            await self._conn.execute(
                "INSERT INTO vote_unlocks(user_id, unlocked_at, expires_at) VALUES(?,?,?) "
                "ON CONFLICT(user_id) DO UPDATE SET unlocked_at=excluded.unlocked_at, expires_at=excluded.expires_at",
                (user_id, now, expires)
            )
            await self._conn.commit()

    async def has_vote_unlock(self, user_id: int) -> bool:
        """Check if user has an active vote unlock."""
        async with self._lock:
            cur = await self._conn.execute(
                "SELECT expires_at FROM vote_unlocks WHERE user_id=?", (user_id,)
            )
            row = await cur.fetchone()
            if not row:
                return False
            if int(time.time()) > row[0]:
                # Expired — clean up
                await self._conn.execute("DELETE FROM vote_unlocks WHERE user_id=?", (user_id,))
                await self._conn.commit()
                return False
            return True

    async def vote_unlock_expires(self, user_id: int) -> int:
        """Returns the Unix timestamp when vote unlock expires, or 0."""
        async with self._lock:
            cur = await self._conn.execute(
                "SELECT expires_at FROM vote_unlocks WHERE user_id=?", (user_id,)
            )
            row = await cur.fetchone()
            return row[0] if row else 0
