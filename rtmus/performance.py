from __future__ import annotations

import asyncio
from time import time
from typing import List, Tuple

from .log import logger
from .midi import MidiOut, c, silence
from .track import Track
from .util import spin_sleep, task_sig


class Performance:
    def __init__(self, out: MidiOut, main_task: task_sig, bpm: float):
        self.out = out
        self.main_task = main_task
        self.last_note = 48
        self.tracks: List[Track] = []
        self._position: int = 0

        self.last = time() + 60 / bpm / 12
        self.delta = 60 / bpm / 24
        self.last_delta = self.delta
        self.bpm = bpm
        self.tick_len = self.delta

    @property
    def position(self):
        return self._position

    def new_track(self, task: task_sig, name="track") -> None:
        self.tracks.append(Track(self, task, name))

    async def start(self) -> None:
        self._position = 0
        self.out.send_message([c.SONG_POSITION, 0, 0])
        await spin_sleep(60 / self.bpm / 24)
        logger.base_time = time()
        self.new_track(self.main_task, "main")
        logger.log("send start")
        self.out.send_message([c.START])
        # Send first clock
        await asyncio.sleep(0.001)
        self.out.send_message([c.CLOCK])
        await spin_sleep(60 / self.bpm / 24)

    async def stop(self) -> None:
        logger.log("cancel tracks")
        for track in self.tracks:
            track.cancel()
        self.tracks = []
        await asyncio.sleep(0)
        logger.log("send stop")
        silence(self.out)

    def tick(self, now: float) -> Tuple[float, float]:
        self._position += 1
        self.delta = now - self.last
        self.last = now
        jitter = 100 / self.tick_len * (self.delta - self.last_delta)
        self.last_delta = self.delta
        self.out.send_message([c.CLOCK])

        for track in self.tracks:
            track.tick(self._position)
        return self.delta, jitter
