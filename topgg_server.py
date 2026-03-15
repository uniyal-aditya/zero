from __future__ import annotations

import asyncio
import json

from aiohttp import web

from db import init_db
from premium_store import record_user_vote
from zero_config import CONFIG


async def handle_topgg(request: web.Request) -> web.Response:
    auth = request.headers.get("Authorization")
    if auth != CONFIG.topgg_webhook_auth:
        return web.Response(status=401, text="Unauthorized")

    data = await request.json()
    user_id = int(data.get("user"))

    conn = await init_db()
    await record_user_vote(conn, user_id)

    return web.Response(status=200, text=json.dumps({"ok": True}))


async def start_topgg_server() -> None:
    if not CONFIG.topgg_webhook_auth:
        print("[top.gg] TOPGG_WEBHOOK_AUTH not set, vote premium will be disabled.")
        return

    app = web.Application()
    app.add_routes([web.post("/topgg", handle_topgg)])

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", CONFIG.topgg_webhook_port)
    await site.start()
    print(
        f"[top.gg] Webhook listening on port {CONFIG.topgg_webhook_port} at path /topgg"
    )


def run_topgg_server_in_background(loop: asyncio.AbstractEventLoop) -> None:
    loop.create_task(start_topgg_server())

