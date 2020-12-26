import asyncio
import gc
from time import time
from typing import List, Optional

import uvloop  # type: ignore

from .log import logger
from .midi import MidiMessage, get_ports
from .performance import Performance
from .track import Track, task_sig
from .util import spin_sleep

Track = Track
odd_time = 11 / 17


def run(task: task_sig, bpm: float) -> None:
    try:
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        asyncio.run(async_main(task, bpm))
    finally:
        logger.flush()


async def async_main(task: task_sig, bpm: float) -> None:
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
    performance = Performance(midi_out, task, bpm)
    try:
        await midi_consumer(queue, performance)
    except asyncio.CancelledError:
        midi_in.cancel_callback()
        await performance.stop()


async def midi_consumer(
    queue: asyncio.Queue[MidiMessage], performance: Performance
) -> None:
    gc_count = gc.collect(1)
    await performance.start()
    tick_delta = 0.0
    tick_jitter = 0.0
    avg_jitter = 0.0
    msg: Optional[List[int]]
    delta: Optional[float]
    while True:
        now = time()
        deadline = now + (60 / performance.bpm / performance.ppb)
        try:
            msg, delta = queue.get_nowait()
        except asyncio.QueueEmpty:
            msg, delta = (None, None)
        tick_delta, tick_jitter = performance.tick(now)
        # We assume that events cluster around pulses so we move gc and printing to an
        # odd moment
        rest = deadline - time()
        delay = rest * odd_time
        if delay > 0:
            await spin_sleep(delay)
        gc_count = gc.collect(1)
        if __debug__:
            pos = performance.position
            avg_jitter += tick_jitter * tick_jitter
            if pos < 10:
                avg_jitter = 0
            if gc_count:
                logger.log(f"gc: {gc_count}")
            if msg:
                logger.log(f"msg: {str(msg):^15}▐delta: {delta:5f}")
            logger.log(
                f"tick delta: {tick_delta:.5f}▐jitter: {tick_jitter:8.3f}%▐"
                f"avg jitter: {avg_jitter/(pos + 10):8.5f}▐pos: {pos}"
            )
        logger.flush()
        rest = deadline - time()
        if rest > 0:
            await spin_sleep(rest)
