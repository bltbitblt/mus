from __future__ import annotations

import asyncio
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
