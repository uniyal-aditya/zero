# keepalive.py
from aiohttp import web
import logging

log = logging.getLogger("zero")

async def health(_):
    return web.Response(text="Zero is alive! 🎵")

async def start_keepalive(port: int = 8080):
    app = web.Application()
    app.router.add_get("/", health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    log.info("Keep-alive server on port %d", port)
