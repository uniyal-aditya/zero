# core/player.py
import asyncio
import wavelink
from typing import Optional, List
import discord

class Queue:
    """Simple wrapper over asyncio.Queue with helpful utilities."""
    def __init__(self):
        self._queue = asyncio.Queue()
        self._list = []  # keep a list for displaying

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
    """
    Custom player extending wavelink.Player
    Provides queue, loop modes, helpers
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.queue = Queue()
        self.loop = "NONE"  # NONE | ONE | ALL
        self._autoplay = False  # reserved
        self.volume = None  # will be set by caller if desired

    async def add_tracks(self, tracks: List[wavelink.Track]):
        """Add many tracks to queue at once."""
        for t in tracks:
            await self.queue.put(t)

    async def add_track(self, track: wavelink.Track):
        await self.queue.put(track)

    async def do_next(self):
        """Play next track according to loop mode."""
        if self.loop == "ONE":
            # replay same track (wavelink requires replaying the track object)
            await self.play(self.current_track)
            return

        if not self.queue.is_empty():
            next_track = await self.queue.get()
            await self.play(next_track)
            return

        if self.loop == "ALL" and len(self.queue) == 0:
            # ALL means we would need to recycle played history - not implemented here
            # For a simple ALL, you can re-add the last playlist externally.
            return

        # nothing left
        await self.stop()
        # optionally disconnect handled by cog

    # Utility for applying a basic EQ (example: bassboost)
    async def set_bassboost(self, strength: float = 0.6):
        """
        Set a simple EQ preset. strength between 0..1
        Note: Requires compatible Lavalink (filters enabled)
        """
        # create bands (example)
        bands = [
            {"band": 0, "gain": int(0 + 10*strength)},  # 60Hz
            {"band": 1, "gain": int(0 + 8*strength)},   # 170Hz
            {"band": 2, "gain": int(0 + 6*strength)},   # 310Hz
            {"band": 3, "gain": int(0 + 4*strength)},
            {"band": 4, "gain": 0},
            {"band": 5, "gain": -2},
            {"band": 6, "gain": -3},
            {"band": 7, "gain": -2},
            {"band": 8, "gain": -1},
            {"band": 9, "gain": 0},
        ]
        await self.set_eq(bands)
