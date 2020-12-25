from rtmus import Task, run
from rtmus.log import logger


async def trick(p: Task):
    while True:
        logger.log("three")
        await p.play(0, 41, 30, 50)


n = 50
x = 1


async def track(p: Task):
    # p.new(trick, "three")
    pos = p.pos
    while True:
        logger.log("4th: {0}", pos)
        # pos = await p.play(0, n, 24 * x, 100, 0.1)
        pos = await p.wait(0.5)


if __name__ == "__main__":
    # Bitwig sync: +38ms
    run(track, 120)
