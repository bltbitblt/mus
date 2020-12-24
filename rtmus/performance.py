"""See the docstring of main()."""
from __future__ import annotations

import asyncio
import traceback
from typing import Awaitable, Callable, List, Tuple

from .log import logger
from .metronome import Metronome
from .midi import (
    ALL_CHANNELS,
    ALL_NOTES_OFF,
    CLOCK,
    CONTROL_CHANGE,
    NOTE_OFF,
    NOTE_ON,
    SONG_POSITION,
    START,
    STOP,
    MidiOut,
)
from .util import spin_sleep


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


class Task:
    def __init__(
        self,
        task: Callable[[Task], Awaitable[None]],
        performance: Performance,
        name="track",
    ):
        self.performance = performance
        self.task = asyncio.create_task(task_handler(task(self), name))
        self.cancel = self.task.cancel
        self.new = performance.new_task

    @property
    def bpm(self):
        return self.performance.bpm

    @bpm.setter
    def bpm(self, value: float):
        self.performance.bpm = value

    async def wait(self, pulses: float) -> None:
        await self.performance.metronome.wait(pulses)

    async def play(
        self,
        channel: int,
        note: int,
        pulses: float,
        volume: int,
        decay: float = 0.5,
    ) -> None:
        out = self.performance.out
        note_on_length = int(round(pulses * decay, 0))
        rest_length = pulses - note_on_length
        out.send_message([NOTE_ON | channel, note, volume])
        await self.wait(note_on_length)
        out.send_message([NOTE_OFF | channel, note, volume])
        await self.wait(rest_length)


class Performance:
    def __init__(
        self, out: MidiOut, track: Callable[[Task], Awaitable[None]], bpm: float
    ):
        self.out = out
        self.track = track
        self.metronome = Metronome(bpm)
        self.last_note = 48
        self.position = 0
        self.tasks: List[Task] = []

    @property
    def bpm(self):
        return self.metronome.bpm

    @bpm.setter
    def bpm(self, value: float):
        self.metronome.bpm = value

    def new_task(self, task: Callable[[Task], Awaitable[None]], name="track") -> None:
        self.tasks.append(Task(task, self, name))

    async def start(self) -> None:
        self.out.send_message([SONG_POSITION, 0, 0])
        await spin_sleep(60 / self.bpm / 24)
        self.new_task(self.track)
        logger.log("send start")
        self.out.send_message([START])
        # Workaround for tempo independent offset due Bitwigs audio-delay-correction
        await asyncio.sleep(0.001)
        self.out.send_message([CLOCK])
        await spin_sleep(60 / self.bpm / 24)

    async def stop(self) -> None:
        logger.log("cancel tasks")
        for task in self.tasks:
            task.cancel()
        self.metronome.stop()
        self.tasks = []
        logger.log("send stop")
        await asyncio.sleep(0)
        out = self.out
        out.send_message([STOP])
        for channel in ALL_CHANNELS:
            out.send_message([CONTROL_CHANGE | channel, ALL_NOTES_OFF, 0])

    async def tick(self, now: float) -> Tuple[float, float]:
        self.out.send_message([CLOCK])
        self.position += 1
        return await self.metronome.tick(now)
