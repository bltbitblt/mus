"""See the docstring of main()."""
from __future__ import annotations

import asyncio
import itertools
import random
import time
from typing import List, Optional, Tuple

import click
import uvloop
from attr import Factory, dataclass

from .metronome import Metronome
from .midi import (ALL_NOTES_OFF, CLOCK, CONTROL_CHANGE, NOTE_OFF, NOTE_ON,
                   START, STOP, MidiOut, get_ports)

# types
EventDelta = float  # in seconds
TimeStamp = float  # time.time()
MidiPacket = List[int]
MidiMessage = Tuple[MidiPacket, EventDelta, TimeStamp]


@dataclass
class Performance:
    out: MidiOut
    metronome: Metronome = Factory(Metronome)
    last_note: int = 48

    async def play(
        self,
        out: MidiOut,
        channel: int,
        note: int,
        pulses: int,
        volume: int,
        decay: float = 0.5,
    ) -> None:
        note_on_length = int(round(pulses * decay, 0))
        rest_length = pulses - note_on_length
        out.send_message([NOTE_ON | channel, note, volume])
        await self.wait(note_on_length)
        out.send_message([NOTE_OFF | channel, note, volume])
        await self.wait(rest_length)

    async def wait(self, pulses: int) -> None:
        await self.metronome.wait(pulses)


@click.command()
def main() -> None:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    asyncio.run(async_main())


async def async_main() -> None:
    queue: asyncio.Queue[MidiMessage] = asyncio.Queue(maxsize=256)
    loop = asyncio.get_event_loop()

    try:
        midi_in, midi_out = get_ports("Virtual", clock_source=True)
    except ValueError as port:
        click.secho(f"{port} not connected", fg="red", err=True)
        raise click.Abort

    def midi_callback(msg, data=None):
        sent_time = time.time()
        midi_message, event_delta = msg
        try:
            loop.call_soon_threadsafe(
                queue.put_nowait, (midi_message, event_delta, sent_time)
            )
        except BaseException as be:
            click.secho(f"callback exc: {type(be)} {be}", fg="red", err=True)

    midi_in.set_callback(midi_callback)
    performance = Performance(midi_out)
    try:
        await midi_consumer(queue, performance)
    except asyncio.CancelledError:
        midi_in.cancel_callback()
        midi_out.send_message([STOP])


async def midi_consumer(
    queue: asyncio.Queue[MidiMessage], performance: Performance
) -> None:
    while True:
        msg, delta, sent_time = await queue.get()
        latency = time.time() - sent_time
        if __debug__:
            print(f"{msg}\tevent delta: {delta:.4f}\tlatency: {latency:.4f}")
        if msg[0] == CLOCK:
            await performance.metronome.tick()
        elif msg[0] == START:
            await performance.metronome.reset()
        elif msg[0] == STOP:
            pass
        elif msg[0] == NOTE_ON:
            performance.last_note = msg[1]


if __name__ == "__main__":
    main()
