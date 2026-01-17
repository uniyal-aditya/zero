# core/player.py
import asyncio
import wavelink
from typing import List

class Queue:
    def __init__(self):
        self._queue = asyncio.Queue()
        self._list = []

    def __len__(self):
        return len(self._list)

    async def put(self, item):
        await self._queue.put(item)
        self._list.append(item)

    async def get(self):
        item = await self._queue.get()
        self._list.pop(0)
        return item

    def clear(self):
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        self._list.clear()

    def is_empty(self):
        return len(self._list) == 0

    def as_list(self):
        return list(self._list)

    def shuffle(self):
        import random
        random.shuffle(self._list)
        # rebuild the queue
        self._queue = asyncio.Queue()
        for item in self._list:
            self._queue.put_nowait(item)

class MusicPlayer(wavelink.Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = Queue()
        self.loop = "NONE"  # NONE | ONE | ALL
        self._history = []  # played tracks history (uris)
        self.volume = None

    async def add_tracks(self, tracks: List[wavelink.Track]):
        for t in tracks:
            await self.queue.put(t)

    async def add_track(self, track: wavelink.Track):
        await self.queue.put(track)

    async def do_next(self):
        # called by on_wavelink_track_end
        if self.loop == "ONE" and self.current_track:
            await self.play(self.current_track)
            return

        if not self.queue.is_empty():
            next_track = await self.queue.get()
            # append to history
            self._history.append(next_track)
            await self.play(next_track)
            return

        if self.loop == "ALL" and len(self._history) > 0:
            # naive ALL implementation: replay history
            for t in list(self._history):
                await self.queue.put(t)

            if not self.queue.is_empty():
                next_track = await self.queue.get()
                await self.play(next_track)
                return

        # nothing left
        await self.stop()
