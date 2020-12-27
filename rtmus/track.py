from __future__ import annotations

import asyncio
import traceback
from random import Random
from typing import TYPE_CHECKING, Awaitable, Iterable, List, Optional, Tuple, Union

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
        self._active: List[Tuple[int, int]] = []

        self.decay: float = 0.5

    def cancel(self, msg: Optional[str] = None) -> None:
        trigger = self._trigger
        if trigger:
            trigger.cancel(msg)
        self._task.cancel(msg)
        self.off_all()
        self._performance.tracks.remove(self)

    def sync(self):
        logger.log("sync {0}", self._name)
        self._position = round(self._position)

    def th(self, n):
        return self.ppa / n

    def bar(self, n):
        return self.ppa * n

    def new(
        self,
        task: task_sig,
        channel: int = 0,
        name="track",
        replace: Optional[Track] = None,
    ) -> Track:
        if replace:
            replace.cancel()
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
            length = self.bar(length * -1)
        else:
            length = self.th(length)
        return await self.wait_l(length)

    async def wait_l(self, pulses: float) -> float:
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

    def cc(self, type: int, value: Union[float, int]):
        self.cc_l(self.channel, type, value)

    def cc_l(self, channel: int, type: int, value: float):
        self.cc_li(channel, type, int(value * 127))

    def cc_li(self, channel: int, type: int, value: int):
        self._out.send_message([c.CONTROL_CHANGE | channel, type, value])

    def on(self, note: int, volume: float = 0.788):
        self.on_l(self.channel, note, volume)

    def on_l(self, channel: int, note: int, volume: float = 0.788):
        self.on_li(channel, note, int(volume * 127))

    def on_li(self, channel: int, note: int, volume: int = 100):
        self._out.send_message([c.NOTE_ON | channel, note, volume])
        self._active.append((channel, note))

    def off_l(self, channel: int, note: int):
        self._out.send_message([c.NOTE_OFF | channel, note, 0])
        self._active.remove((channel, note))

    def off(self, channel: int, note: int):
        self.off_l(self.channel, note)

    def off_all(self):
        for channel, note in self._active:
            self._out.send_message([c.NOTE_OFF | channel, note, 0])
        self._active.clear()

    async def play(
        self,
        note: Union[int, Iterable[int]],
        length: float,
        volume: float = 0.788,
        decay: Optional[float] = None,
    ) -> float:
        if decay is None:
            decay = self.decay
        if length < 0:
            length = self.bar(length * -1)
        else:
            length = self.th(length)
        return await self.play_l(self.channel, note, length, volume, decay)

    async def play_l(
        self,
        channel: int,
        notes: Union[int, Iterable[int]],
        pulses: float,
        volume: float = 0.788,
        decay: float = 0.5,
    ) -> float:
        note_on_length = pulses * decay
        rest_length = pulses - note_on_length
        if isinstance(notes, int):
            notes = [notes]
        for note in notes:
            self.on_l(channel, note, volume)
        await self.wait_l(note_on_length)
        for note in notes:
            self.off_l(channel, note)
        return await self.wait_l(rest_length)
