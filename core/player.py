# core/player.py
import asyncio
import wavelink
from typing import List, Optional

class SimpleQueue:
    def __init__(self):
        self._list: List = []
        self._lock = asyncio.Lock()
        self._queue = asyncio.Queue()

    async def put(self, item):
        async with self._lock:
            self._list.append(item)
            await self._queue.put(item)

    async def get(self):
        item = await self._queue.get()
        return item

    def as_list(self):
        return list(self._list)

    def is_empty(self):
        return len(self._list) == 0

    def clear(self):
        self._list.clear()
        # recreate the queue
        self._queue = asyncio.Queue()

class MusicPlayer(wavelink.Player):
    """
    Simple player wrapper - expects wavelink Player methods: play, stop, pause, resume, volume, seek.
    The wavelink Player instance will be used as the voice client.
    """

    def __init__(self, bot, guild_id: int):
        super().__init__(bot=bot, guild_id=guild_id)
        self.queue = SimpleQueue()
        self.current_track = None
        self._history: List = []
        self.loop_mode = "off"  # off / track / queue

    async def put(self, track):
        await self.queue.put(track)

    async def play_next(self, track):
        await self.play(track)
        self.current_track = track

    async def do_next(self):
        # called when current track ends
        try:
            if self.loop_mode == "track" and self.current_track:
                await self.play(self.current_track)
                return
            if not self.queue.is_empty():
                nxt = await self.queue.get()
                # pop first element from list
                try:
                    self.queue._list.pop(0)
                except Exception:
                    pass
                # push current into history
                if self.current_track:
                    self._history.append(self.current_track)
                self.current_track = nxt
                await self.play(nxt)
        except Exception:
            # don't crash: log to stdout
            import traceback
            traceback.print_exc()
