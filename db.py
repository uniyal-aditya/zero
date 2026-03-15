from __future__ import annotations

import aiosqlite

DB_PATH = "zero_python.db"


async def init_db() -> aiosqlite.Connection:
    conn = await aiosqlite.connect(DB_PATH)
    await conn.execute("PRAGMA journal_mode=WAL;")

    await conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS premium_servers (
            guild_id TEXT PRIMARY KEY,
            granted_by TEXT NOT NULL,
            granted_at INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS premium_votes (
            user_id TEXT PRIMARY KEY,
            last_vote_at INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT NOT NULL,
            owner_id TEXT NOT NULL,
            name TEXT NOT NULL,
            UNIQUE (guild_id, owner_id, name)
        );

        CREATE TABLE IF NOT EXISTS playlist_tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            playlist_id INTEGER NOT NULL,
            url TEXT NOT NULL,
            title TEXT,
            added_at INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS liked_tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            url TEXT NOT NULL,
            title TEXT,
            liked_at INTEGER NOT NULL
        );
        """
    )

    await conn.commit()
    return conn

