import asyncio

from rtmus import Task, run
from rtmus.log import logger


async def trick(p: Task):
    while True:
        logger.log("three")
        await p.play(0, 41, 30, 50)


async def track(p: Task):
    # p.new(trick, "three")
    while True:
        logger.log("beat")
        logger.log("4th")
        await p.play(0, 48, 24, 100)
        logger.log("4th")
        await p.play(0, 48, 24, 100)
        logger.log("4th")
        await p.play(0, 48, 24, 100)
        logger.log("4th")
        await p.play(0, 48, 24, 100)


if __name__ == "__main__":
    run(track, 90.05)
