import asyncio
import gc
import traceback
from time import time
from typing import Awaitable, Callable, Optional

import uvloop  # type: ignore

from .log import logger
from .midi import (CLOCK, CONTINUE, NOTE_ON, SONG_POSITION, START, STOP,
                   MidiMessage, get_ports)
from .performance import Performance


def run(track: Callable[[Performance], Awaitable[None]], bpm: float) -> None:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    asyncio.run(async_main(track, bpm))


async def async_main(
    track: Callable[[Performance], Awaitable[None]], bpm: float
) -> None:
    queue: asyncio.Queue[MidiMessage] = asyncio.Queue(maxsize=256)
    loop = asyncio.get_event_loop()

    try:
        midi_in, midi_out = get_ports("Virtual")
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
    performance = Performance(midi_out, track, bpm)
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
    while True:
        deadline = time() + (60 / performance.bpm / 24)
        try:
            msg, delta = await queue.get_nowait()
        except asyncio.QueueEmpty:
            msg, delta = (None, None)
        tick_delta, tick_jitter = await performance.tick()
        gc_count = gc.collect(1)
        if __debug__:
            if gc_count:
                logger.log(f"gc: {gc_count}")
            if msg:
                logger.log("msg: {str(msg):^15}▐delta: {delta:5f}")
            logger.log(
                f"tick delta: {tick_delta:.5f}▐jitter: {tick_jitter:7.3f}ms▐"
                f"pos: {performance.position}"
            )
        rest = deadline - time()
        if rest > 0:
            await asyncio.sleep(rest)
