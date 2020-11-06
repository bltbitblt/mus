import asyncio
import time
import traceback
from typing import Awaitable, Callable, Optional

import click
import uvloop  # type: ignore

from .midi import CLOCK, NOTE_ON, START, STOP, MidiMessage, get_ports
from .performance import Performance


def run(track: Callable[[Performance], Awaitable[None]]) -> None:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    asyncio.run(async_main(track))


async def async_main(track: Callable[[Performance], Awaitable[None]]) -> None:
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
        performance.stop()
        midi_out.send_message([STOP])


async def _print_exceptions(task):
    try:
        print("track start")
        await task
    except asyncio.CancelledError:
        print("track stop")
        raise
    except Exception:
        print("exec")
        traceback.print_exc()
        raise


async def midi_consumer(
    queue: asyncio.Queue[MidiMessage], performance: Performance
) -> None:
    tick_delta = 0.0
    track: Optional[asyncio.Task] = None
    while True:
        msg, delta, sent_time = await queue.get()
        if __debug__:
            latency = time.time() - sent_time
        if msg[0] == CLOCK:
            tick_delta = await performance.metronome.tick()
        elif msg[0] == START:
            print("midi start")
            await performance.metronome.reset()
            track = asyncio.create_task(
                _print_exceptions(performance.track(performance))
            )
        elif msg[0] == STOP:
            print("midi stop")
            if track:
                track.cancel()
                track = None
            performance.stop()
        elif msg[0] == NOTE_ON:
            performance.last_note = msg[1]
        if __debug__:
            print(
                f"{msg}\tevent delta: {delta:.4f}\t"
                f"tick delta: {tick_delta:.4f}\tlatency: {latency:.4f}"
            )
