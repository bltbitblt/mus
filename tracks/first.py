from rtmus import Track, run
from rtmus.log import logger


async def trick(p: Track):
    while True:
        logger.log("three: {0}", p.pos)
        await p.play(0, 60, 32, 100, 1 / 6)


n = 50


async def track(p: Track):
    # p.new(trick, "three")
    while True:
        p.sync()
        logger.log("4th: {0}", p.pos)
        # await p.play(0, n, p.th(4), 100, 1 / 6)
        pos = await p.play(0, n, p.ppb - (1 / 3), 100, 1 / 6)
        logger.log("wait: {0}", pos)
        pos = await p.wait(1 / 3)


if __name__ == "__main__":
    # Bitwig sync: +38ms
    run(track, 120)
