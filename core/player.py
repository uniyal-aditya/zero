# core/player.py
import asyncio
import wavelink

class SimpleQueue:
    def __init__(self):
        self._list = []
        self._lock = asyncio.Lock()
        self._queue = asyncio.Queue()

    async def put(self, item):
        async with self._lock:
            self._list.append(item)
            await self._queue.put(item)

    async def get(self):
        return await self._queue.get()

    def as_list(self):
        return list(self._list)

    def is_empty(self):
        return len(self._list) == 0

    def clear(self):
        self._list.clear()
        # reset queue
        self._queue = asyncio.Queue()

    def add_tracks(self, tracks):
        for t in tracks:
            self._list.append(t)
            self._queue.put_nowait(t)

class MusicPlayer(wavelink.Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = SimpleQueue()
        self._history = []

    async def do_next(self):
        # Called when a track ends
        if not self.queue.is_empty():
            nxt = await self.queue.get()
            # remove from list front
            try:
                self.queue._list.pop(0)
            except Exception:
                pass
            # push current to history if exists
            if self.current_track:
                self._history.append(self.current_track)
            await self.play(nxt)
