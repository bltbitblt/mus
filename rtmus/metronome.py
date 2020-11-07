from __future__ import annotations

import asyncio
from time import time
from typing import List, Tuple

from attr import Factory, dataclass


class Countdown(asyncio.Future):
    def __init__(self, value: int, *, loop=None) -> None:
        super().__init__(loop=loop)
        self._value = value

    def tick(self) -> None:
        self._value -= 1
        if self._value == 0 and not self.done():
            self.set_result(None)


@dataclass
class Metronome:
    last: float = time()
    delta: float = 0.02  # 125 BPM (0.02 / 60 / 24 pulses per quarter note)
    last_delta: float = 0.0
    countdowns: List[Countdown] = Factory(list)
    bar: asyncio.Event = Factory(asyncio.Event)

    async def wait(self, pulses: int) -> None:
        if pulses == 0:
            return
        countdown = Countdown(pulses)
        self.countdowns.append(countdown)
        await countdown

    def reset(self) -> None:
        self.bar.clear()
        for countdown in self.countdowns:
            if not countdown.done():  # could have been cancelled by CTRL-C
                countdown.cancel()
        self.countdowns = []

    async def tick(self) -> Tuple[float, float]:
        tick_time = time()
        self.delta = tick_time - self.last
        self.last = tick_time
        jitter = (self.last_delta - self.delta) * 1000
        self.last_delta = self.delta
        done_indexes: List[int] = []
        for index, countdown in enumerate(self.countdowns):
            countdown.tick()
            if countdown.done():
                done_indexes.append(index)
        for index in reversed(done_indexes):
            del self.countdowns[index]
        return self.delta, jitter
