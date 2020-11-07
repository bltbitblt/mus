import asyncio

from rtmus import Task, run
from rtmus.log import logger


async def trick(p: Task):
    while True:
        logger.log("tree")
        await p.play(0, 48, 30, 10)


async def track(p: Task):
    try:
        p.new(trick)
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
    except asyncio.CancelledError:
        logger.log("track stop")
    pass


if __name__ == "__main__":
    run(track, 120)
