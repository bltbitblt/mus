from __future__ import annotations

import asyncio
import math
from time import time
from typing import TYPE_CHECKING, Awaitable, Callable

if TYPE_CHECKING:
    from .track import Track

task_sig = Callable[["Track"], Awaitable[None]]
sleep_resolution = 0.001


async def spin_sleep(sleep_time):
    deadline = sleep_time + time()
    await asyncio.sleep(sleep_time - sleep_resolution)
    while deadline > time():
        await asyncio.sleep(0)


def note_to_hz(note: float) -> float:
    return 440.0 * (2.0 ** ((note - 69) / 12.0))


def hz_to_note(frequency: float) -> float:
    return 12 * (math.log2(frequency) - math.log2(440.0)) + 69


def note_to_name(note: int) -> str:
    semis = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

    note = int(round(note))

    return "%s%s" % (semis[note % 12], str(note // 12 - 1))


def note_to_name_flat(note: int) -> str:
    semis = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

    note = int(round(note))

    return "%s%s" % (semis[note % 12], str(note // 12 - 1))


def name_to_note(name: str) -> int:
    pitch_map = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    accent_map = {"#": 1, "b": -1}

    pitch = pitch_map[name[0]]
    accent = accent_map.get(name[1])
    octave_index = 2
    if accent is None:
        accent = 0
        octave_index = 1
    octave = int(name[octave_index:])

    return 12 * (octave + 1) + pitch + accent
