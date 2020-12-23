import asyncio
from time import time

spin_resolution = 0.001


async def spin_sleep(sleep_time):
    deadline = sleep_time + time()
    await asyncio.sleep(sleep_time - spin_resolution)
    while deadline > time():
        await asyncio.sleep(0)
