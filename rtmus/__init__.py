import asyncio
import gc
from time import time
from typing import Awaitable, Callable, List, Optional

import uvloop  # type: ignore

from .log import logger
from .midi import MidiMessage, get_ports
from .performance import Performance, Task


def run(track: Callable[[Task], Awaitable[None]], bpm: float) -> None:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    asyncio.run(async_main(track, bpm))


async def async_main(track: Callable[[Task], Awaitable[None]], bpm: float) -> None:
    queue: asyncio.Queue[MidiMessage] = asyncio.Queue(maxsize=256)
    loop = asyncio.get_event_loop()

    try:
        midi_in, midi_out = get_ports("Virtual")
    except ValueError as port:
        print(f"{port} not connected")
        raise

    def midi_callback(msg, data=None):
        msg, event_delta = msg
        try:
            loop.call_soon_threadsafe(queue.put_nowait, (msg, event_delta))
        except BaseException as be:
            print(f"callback exc: {type(be)} {be}")

    midi_in.set_callback(midi_callback)
    performance = Performance(midi_out, track, bpm)
    try:
        await midi_consumer(queue, performance)
    except asyncio.CancelledError:
        midi_in.cancel_callback()
        performance.stop()


async def midi_consumer(
    queue: asyncio.Queue[MidiMessage], performance: Performance
) -> None:
    await performance.start()
    tick_delta = 0.0
    tick_jitter = 0.0
    msg: Optional[List[int]]
    delta: Optional[float]
    while True:
        now = time()
        deadline = now + (60 / performance.bpm / 24)
        try:
            msg, delta = queue.get_nowait()
        except asyncio.QueueEmpty:
            msg, delta = (None, None)
        tick_delta, tick_jitter = await performance.tick(now)
        gc_count = gc.collect(1)
        if __debug__:
            if gc_count:
                logger.log(f"gc: {gc_count}")
            if msg:
                logger.log(f"msg: {str(msg):^15}▐delta: {delta:5f}")
            logger.log(
                f"tick delta: {tick_delta:.5f}▐jitter: {tick_jitter:7.3f}ms▐"
                f"pos: {performance.position}"
            )
        rest = deadline - time()
        if rest > 0:
            await performance.spin_sleep(rest)
