from __future__ import annotations

import time
from typing import Optional

import aiosqlite

from zero_config import CONFIG


async def grant_server_premium(conn: aiosqlite.Connection, guild_id: int, granted_by: int) -> None:
    if granted_by != CONFIG.owner_id:
        raise PermissionError("Only the bot owner can grant permanent server premium.")

    await conn.execute(
        """
        INSERT INTO premium_servers (guild_id, granted_by, granted_at)
        VALUES (?, ?, ?)
        ON CONFLICT(guild_id) DO UPDATE SET
            granted_by = excluded.granted_by,
            granted_at = excluded.granted_at
        """,
        (str(guild_id), str(granted_by), int(time.time())),
    )
    await conn.commit()


async def is_guild_premium(conn: aiosqlite.Connection, guild_id: int) -> bool:
    async with conn.execute(
        "SELECT guild_id FROM premium_servers WHERE guild_id = ?", (str(guild_id),)
    ) as cur:
        row = await cur.fetchone()
        return row is not None


async def record_user_vote(conn: aiosqlite.Connection, user_id: int) -> None:
    await conn.execute(
        """
        INSERT INTO premium_votes (user_id, last_vote_at)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET last_vote_at = excluded.last_vote_at
        """,
        (str(user_id), int(time.time())),
    )
    await conn.commit()


async def has_active_vote_premium(conn: aiosqlite.Connection, user_id: int) -> bool:
    async with conn.execute(
        "SELECT last_vote_at FROM premium_votes WHERE user_id = ?", (str(user_id),)
    ) as cur:
        row: Optional[tuple] = await cur.fetchone()
        if row is None:
            return False
        last_vote_at = int(row[0])
    return time.time() - last_vote_at < CONFIG.premium_vote_duration_sec


async def is_user_premium_in_guild(
    conn: aiosqlite.Connection, user_id: int, guild_id: int
) -> bool:
    if await is_guild_premium(conn, guild_id):
        return True
    return await has_active_vote_premium(conn, user_id)

