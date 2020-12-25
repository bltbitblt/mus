from __future__ import annotations

import asyncio
from time import time
from typing import List, Tuple

from .util import sleep_resolution, spin_sleep

spin_sleep_threshold = 1.0 + 2 * sleep_resolution


class Countdown(asyncio.Future):
    def __init__(self, value: float, *, loop=None) -> None:
        super().__init__(loop=loop)
        self._value = value
        self._scheduled = False

    async def resolve(self, bpm: float, position: float):
        deadline = 60 / bpm / 24 * self._value
        await spin_sleep(deadline)
        self.set_result(position + self._value)

    async def tick(self, tasks, bpm: float, position: int):
        self._value -= 1
        if (
            self._value < spin_sleep_threshold
            and not self._scheduled
            and not self.done()
        ):
            self._scheduled = True
            tasks.append(asyncio.create_task(self.resolve(bpm, position)))


class Metronome:
    def __init__(self, bpm):
        self.last = time() + 60 / bpm / 12
        self.delta = 60 / bpm / 24
        self.last_delta = self.delta
        self._bpm = bpm
        self.tick_len = self.delta
        self.countdowns: List[Countdown] = []
        self.position: int = 0
        self.tasks = []

    @property
    def bpm(self) -> float:
        return self._bpm

    @bpm.setter
    def bpm(self, value: float):
        self._bpm = value
        self.tick_len = 60 / value / 24

    async def wait(self, pulses: float) -> float:
        if pulses < spin_sleep_threshold:
            await spin_sleep(60 / self.bpm / 24 * pulses)
            return self.position + pulses
        else:
            countdown = Countdown(pulses)
            self.countdowns.append(countdown)
            return await countdown

    def start(self):
        self.position = 1

    def stop(self):
        for task in self.tasks:
            task.cancel()
        self.tasks = []
        for countdown in self.countdowns:
            if not countdown.done():  # could have been cancelled by CTRL-C
                countdown.cancel()
        self.countdowns = []

    async def tick(self, now: float) -> Tuple[float, float]:
        self.position += 1
        self.delta = now - self.last
        self.last = now
        jitter = 100 / self.tick_len * (self.delta - self.last_delta)
        self.last_delta = self.delta
        done_indexes: List[int] = []
        for index, countdown in enumerate(self.countdowns):
            await countdown.tick(self.tasks, self.bpm, self.position)
            if countdown.done():
                done_indexes.append(index)
        for index in reversed(done_indexes):
            del self.countdowns[index]
        return self.delta, jitter
