from rtmus import Task, run
from rtmus.log import logger


async def trick(p: Task):
    while True:
        logger.log("three")
        await p.play(0, 41, 30, 50)


n = 50


async def track(p: Task):
    # p.new(trick, "three")
    pos = p.pos
    while True:
        logger.log("4th: {0}", pos)
        pos = await p.play(0, n, 24, 100, 0.1)
        # pos = await p.play(0, n, 12, 100, 0.1)
        # logger.log("wait: {0}", pos)
        # pos = await p.wait(12)


if __name__ == "__main__":
    # Bitwig sync: +38ms
    run(track, 120)
