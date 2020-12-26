from __future__ import annotations

import asyncio
import traceback
from random import Random
from typing import TYPE_CHECKING, Awaitable, Optional, Union

from .log import logger
from .midi import c
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
    future: asyncio.Future, position: int, deadline: float, bpm: float, ppb: int
):
    pulses = deadline - position
    await spin_sleep(60 / bpm / ppb * pulses)
    future.set_result(deadline)


class Track:
    def __init__(
        self,
        performance: Performance,
        task: task_sig,
        channel: int = 0,
        position: float = 0,
        name: str = "track",
    ):
        self._performance = performance
        self._task = asyncio.create_task(task_handler(task(self), name))
        self.channel = channel
        self._position: float = position
        self._name = name
        self._future: Optional[asyncio.Future] = None
        self._trigger: Optional[asyncio.Task] = None
        self._deadline: float = 0
        self._out = performance.out
        self.c = c
        self.r = Random(1)
        self.last_note: int = 48
        self.last_channel: int = channel

        self.decay: float = 0.5

    def cancel(self, msg: Optional[str] = None) -> None:
        trigger = self._trigger
        if trigger:
            trigger.cancel(msg)
        self._task.cancel(msg)
        self._out.send_message([c.NOTE_OFF | self.last_channel, self.last_note, 0])

    def sync(self):
        self._position = round(self._position)

    def th(self, n):
        return self.ppa / n

    def bar(self, n):
        return self.ppa * n

    def new(self, task: task_sig, channel: int = 0, name="track") -> Track:
        return self._performance.new_track(
            task, channel=channel, position=self._position, name=name
        )

    @property
    def out(self):
        return self._out

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
    def ppb(self):
        return self._performance.pulses_per_beat

    @property
    def ppa(self):
        return self._performance.pulses_per_bar

    @property
    def bpm(self):
        return self._performance.bpm

    @bpm.setter
    def bpm(self, value: float):
        self._performance.bpm = value

    async def wait(self, length) -> float:
        if length < 0:
            length = self.bar(length)
        else:
            length = self.th(length)
        return await self.wait_lowlevel(length)

    async def wait_lowlevel(self, pulses: float) -> float:
        if self._future:
            raise RuntimeError(f"Track {self.name} is already waiting")
        if pulses > spin_sleep_threshold:
            self._deadline = self._position + pulses
            self._future = asyncio.Future()
            self._position = await self._future
        else:
            await spin_sleep(60 / self.bpm / self.ppb * pulses)
            self._position += pulses
        return self._position

    def tick(self, position: int) -> None:
        if self._future and position > (self._deadline - spin_sleep_threshold):
            future = self._future
            self._future = None
            self.trigger = asyncio.create_task(
                trigger_deadline(future, position, self._deadline, self.bpm, self.ppb),
                name="trigger_deadline",
            )

    async def play(
        self,
        note: int,
        length: float,
        volume: float = 0.788,
        decay: Optional[float] = None,
    ) -> float:
        if decay is None:
            decay = self.decay
        if length < 0:
            length = self.bar(length)
        else:
            length = self.th(length)
        return await self.play_lowlevel(
            self.channel, note, length, int(127 * volume), decay
        )

    def cc(self, type: int, value: Union[float, int]):
        if isinstance(value, float):
            value = int(127 * value)
        self.cc_lowlevel(self.channel, type, value)

    def cc_lowlevel(self, channel: int, type: int, value: int):
        self._out.send_message([c.CONTROL_CHANGE | channel, type, value])

    async def play_lowlevel(
        self,
        channel: int,
        note: int,
        pulses: float,
        volume: int,
        decay: float = 0.5,
    ) -> float:
        out = self._out
        self.last_note = note
        self.last_channel = channel
        note_on_length = pulses * decay
        rest_length = pulses - note_on_length
        out.send_message([c.NOTE_ON | channel, note, volume])
        await self.wait_lowlevel(note_on_length)
        out.send_message([c.NOTE_OFF | channel, note, volume])
        return await self.wait_lowlevel(rest_length)
