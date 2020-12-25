from __future__ import annotations

import asyncio
import traceback
from typing import TYPE_CHECKING, Awaitable, Optional

from .log import logger
from .midi import NOTE_OFF, NOTE_ON
from .util import sleep_resolution, spin_sleep, task_sig

if TYPE_CHECKING:
    from .performance import Performance

spin_sleep_threshold = 1.0 + 2 * sleep_resolution


async def task_handler(task: Awaitable[None], name):
    try:
        logger.log(f"{name} start")
        await task
    except asyncio.CancelledError:
        logger.log(f"{name} stop")
        raise
    except Exception:
        logger.log(f"{name} exception")
        traceback.print_exc()
        raise


async def trigger_deadline(
    future: asyncio.Future, position: int, deadline: float, bpm: float
):
    delay = deadline - position
    await spin_sleep(60 / bpm / 24 * delay)
    future.set_result(deadline)


class Track:
    def __init__(
        self,
        performance: Performance,
        task: task_sig,
        name="track",
    ):
        self._performance = performance
        self._task = asyncio.create_task(task_handler(task(self), name))
        self.cancel = self.task.cancel
        self.new = performance.new_track
        self._name = name
        self._future: Optional[asyncio.Future] = None
        self._deadline: float = 0
        self._position: float = 0

    @property
    def task(self):
        return self._task

    @property
    def name(self):
        return self._name

    @property
    def position(self):
        return self._position

    @property
    def pos(self):
        return self._position

    @property
    def waiting(self):
        return bool(self._future)

    @property
    def deadline(self):
        return self._deadline

    @property
    def bpm(self):
        return self._performance.bpm

    @bpm.setter
    def bpm(self, value: float):
        self._performance.bpm = value

    async def wait(self, pulses: float) -> float:
        if self._future:
            raise RuntimeError(f"Track {self.name} is already waiting")
        self._deadline = self._position + pulses
        self._future = asyncio.Future()
        self._position = await self._future
        return self._position

    def tick(self, position: int) -> None:
        if self._future and position > (self._deadline - spin_sleep_threshold):
            future = self._future
            self._future = None
            asyncio.create_task(
                trigger_deadline(future, position, self._deadline, self.bpm),
                name="trigger_deadline",
            )

    async def play(
        self,
        channel: int,
        note: int,
        pulses: float,
        volume: int,
        decay: float = 0.5,
    ) -> float:
        out = self._performance.out
        note_on_length = pulses * decay
        rest_length = pulses - note_on_length
        out.send_message([NOTE_ON | channel, note, volume])
        await self.wait(note_on_length)
        out.send_message([NOTE_OFF | channel, note, volume])
        return await self.wait(rest_length)