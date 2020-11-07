"""See the docstring of main()."""
from __future__ import annotations

import asyncio
import traceback
from time import time
from typing import Awaitable, Callable, List, Tuple

from attr import Factory, dataclass

from .log import logger
from .metronome import Metronome
from .midi import (ALL_CHANNELS, ALL_NOTES_OFF, CLOCK, CONTROL_CHANGE,
                   NOTE_OFF, NOTE_ON, START, STOP, MidiOut)

_resolution = 0.001


async def task_handler(t):
    try:
        logger.log("track start")
        await t
    except asyncio.CancelledError:
        logger.log("track stop")
        raise
    except Exception:
        logger.log("exception")
        traceback.print_exc()
        raise


@dataclass
class Performance:
    out: MidiOut
    track: Callable[[Performance], Awaitable[None]]
    bpm: float = 120
    metronome: Metronome = Factory(Metronome)
    last_note: int = 48
    position: int = 0
    tasks: List[asyncio.Task] = []

    async def play(
        self,
        channel: int,
        note: int,
        pulses: int,
        volume: int,
        decay: float = 0.5,
    ) -> None:
        out = self.out
        note_on_length = int(round(pulses * decay, 0))
        rest_length = pulses - note_on_length
        out.send_message([NOTE_ON | channel, note, volume])
        await self.wait(note_on_length)
        out.send_message([NOTE_OFF | channel, note, volume])
        await self.wait(rest_length)

    async def wait(self, pulses: int) -> None:
        await self.metronome.wait(pulses)

    def task(self, task: Awaitable[None]) -> None:
        self.tasks.append(asyncio.create_task(task_handler(task)))

    def start(self) -> None:
        self.out.send_message([START])

    def stop(self) -> None:
        for task in self.tasks:
            task.cancel()
        out = self.out
        out.send_message([STOP])
        for channel in ALL_CHANNELS:
            out.send_message([CONTROL_CHANGE | channel, ALL_NOTES_OFF, 0])

    async def tick(self, now: float) -> Tuple[float, float]:
        self.out.send_message([CLOCK])
        self.position += 1
        return await self.metronome.tick(now)

    async def spin_sleep(self, sleep_time):
        deadline = sleep_time + time()
        await asyncio.sleep(sleep_time - _resolution)
        while deadline > time():
            await asyncio.sleep(0)
