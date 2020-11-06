import asyncio
import gc
import traceback
from typing import Awaitable, Callable, Optional

import click
import uvloop  # type: ignore

from .log import logger
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
        midi_message, event_delta = msg
        try:
            loop.call_soon_threadsafe(queue.put_nowait, (midi_message, event_delta))
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
        logger.log("track start")
        await task
    except asyncio.CancelledError:
        logger.log("track stop")
        raise
    except Exception:
        logger.log("exception")
        traceback.print_exc()
        raise


async def midi_consumer(
    queue: asyncio.Queue[MidiMessage], performance: Performance
) -> None:
    track: Optional[asyncio.Task] = None
    tick_delta = 0.0
    tick_jitter = 0.0
    while True:
        msg, delta = await queue.get()
        if msg[0] == CLOCK:
            tick_delta, tick_jitter = await performance.metronome.tick()
        elif msg[0] == START:
            logger.log("midi start")
            track = asyncio.create_task(
                _print_exceptions(performance.track(performance))
            )
            performance.metronome.reset()
        elif msg[0] == STOP:
            logger.log("midi stop")
            if track:
                track.cancel()
                track = None
            performance.stop()
        elif msg[0] == NOTE_ON:
            performance.last_note = msg[1]
        gc_count = gc.collect(1)
        if __debug__:
            if gc_count:
                logger.log(f"gc: {gc_count}")
            pos = performance.metronome.position
            logger.log(
                f"msg: {str(msg):^15}▐event delta: {delta:.5f}▐"
                f"tick delta: {tick_delta:.5f}▐jitter: {tick_jitter:7.3f}ms▐pos: {pos}"
            )
