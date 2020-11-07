import asyncio
import gc
import traceback
from typing import Awaitable, Callable, Optional

import uvloop  # type: ignore

from .log import logger
from .midi import (CLOCK, CONTINUE, NOTE_ON, SONG_POSITION, START, STOP,
                   MidiMessage, get_ports)
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
        print(f"{port} not connected", fg="red", err=True)
        raise

    def midi_callback(msg, data=None):
        msg, event_delta = msg
        try:
            loop.call_soon_threadsafe(queue.put_nowait, (msg, event_delta))
        except BaseException as be:
            print(f"callback exc: {type(be)} {be}", fg="red", err=True)

    midi_in.set_callback(midi_callback)
    performance = Performance(midi_out, track)
    try:
        await midi_consumer(queue, performance)
    except asyncio.CancelledError:
        midi_in.cancel_callback()
        performance.stop()
        midi_out.send_message([STOP])


async def task(t):
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


async def midi_consumer(
    queue: asyncio.Queue[MidiMessage], performance: Performance
) -> None:
    track: Optional[asyncio.Task] = None
    tick_delta = 0.0
    tick_jitter = 0.0
    metronome = performance.metronome
    while True:
        msg, delta = await queue.get()
        start = False
        if msg[0] == CLOCK:
            tick_delta, tick_jitter = await performance.metronome.tick()
        elif msg[0] == STOP:
            logger.log("midi STOP")
            if track:
                track.cancel()
                track = None
                performance.stop()
        elif msg[0] == START:
            logger.log("midi START")
            start = True
            metronome.position = 0
        elif msg[0] == CONTINUE:
            logger.log("midi CONTINUE")
            start = True
        elif msg[0] == SONG_POSITION:
            metronome.position = ((msg[2] << 7) + msg[1]) * 6
            logger.log(f"midi SONG_POSITION: {metronome.position}")
            start = True
        elif msg[0] == NOTE_ON:
            performance.last_note = msg[1]
        if start and not track:
            metronome.reset()
            track = asyncio.create_task(task(performance.track(performance)))
        gc_count = gc.collect(1)
        if __debug__:
            if gc_count:
                logger.log(f"gc: {gc_count}")
            pos = metronome.position
            logger.log(
                f"msg: {str(msg):^15}▐event delta: {delta:.5f}▐"
                f"tick delta: {tick_delta:.5f}▐jitter: {tick_jitter:7.3f}ms▐pos: {pos}"
            )
