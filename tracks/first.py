import asyncio

from rtmus import Performance, run
from rtmus.log import logger


async def track(p: Performance):
    try:
        while True:
            await p.metronome.bar.wait()
            logger.log("beat")
            logger.log("4th")
            await p.play(0, 48, 24, 100)
            logger.log("4th")
            await p.play(0, 48, 24, 100)
            logger.log("4th")
            await p.play(0, 48, 24, 100)
            logger.log("4th")
            await p.play(0, 48, 22, 100)
    except asyncio.CancelledError:
        logger.log("track stop")
    pass


if __name__ == "__main__":
    run(track)
