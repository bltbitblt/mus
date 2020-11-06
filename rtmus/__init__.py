import asyncio
import time
from typing import Awaitable

import click
import uvloop  # type: ignore

from .midi import (ALL_CHANNELS, ALL_NOTES_OFF, CLOCK, CONTROL_CHANGE, NOTE_ON,
                   START, STOP, MidiMessage, get_ports)
from .performance import Performance


def run(track: Awaitable[Performance]) -> None:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    asyncio.run(async_main(track))


async def async_main(track: Awaitable[Performance]) -> None:
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
    performance = Performance(midi_out, track)
    try:
        await midi_consumer(queue, performance)
    except asyncio.CancelledError:
        midi_in.cancel_callback()
        for channel in ALL_CHANNELS:
            midi_out.send_message([CONTROL_CHANGE | channel, ALL_NOTES_OFF, 0])
        midi_out.send_message([STOP])


async def midi_consumer(
    queue: asyncio.Queue[MidiMessage], performance: Performance
) -> None:
    tick_delta = 0.0
    while True:
        msg, delta, sent_time = await queue.get()
        latency = time.time() - sent_time
        if msg[0] == CLOCK:
            tick_delta = await performance.metronome.tick()
        elif msg[0] == START:
            await performance.metronome.reset()
        elif msg[0] == STOP:
            pass
        elif msg[0] == NOTE_ON:
            performance.last_note = msg[1]
        if __debug__:
            print(
                f"{msg}\tevent delta: {delta:.4f}\t"
                f"tick delta: {tick_delta:.4f}\tlatency: {latency:.4f}"
            )
