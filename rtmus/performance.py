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

        self.beats_per_bar = 4
        self.pulses_per_beat = 24
        self.last = time() + 60 / bpm / self.ppb * 2
        self.delta = 60 / bpm / self.ppb
        self.last_delta = self.delta
        self.bpm = bpm
        self.tick_len = self.delta

    @property
    def ppb(self):
        return self.pulses_per_beat

    @property
    def ppa(self):
        return self.pulses_per_beat * self.beats_per_bar

    @property
    def pulses_per_bar(self):
        return self.pulses_per_beat * self.beats_per_bar

    @property
    def position(self):
        return self._position

    def new_track(
        self, task: task_sig, channel: int = 0, position: float = 0, name="track"
    ) -> Track:
        track = Track(self, task, channel, position, name)
        self.tracks.append(track)
        return track

    async def start(self) -> None:
        self._position = 0
        self.out.send_message([c.SONG_POSITION, 0, 0])
        await spin_sleep(60 / self.bpm / self.ppb)
        logger.base_time = time()
        self.new_track(self.main_task, name="main")
        logger.log("send start")
        self.out.send_message([c.START])
        self.out.send_message([c.CLOCK])
        await spin_sleep(60 / self.bpm / self.ppb)

    async def stop(self) -> None:
        logger.log("cancel tracks")
        for track in self.tracks:
            track.cancel()
        self.tracks = []
        await asyncio.sleep(0)
        logger.log("send stop")
        silence(self.out)
        await asyncio.sleep(0.001)

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
