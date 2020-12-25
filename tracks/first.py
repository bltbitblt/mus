from rtmus import Track, run
from rtmus.log import logger


async def trick(p: Track):
    while True:
        logger.log("three: {0}", p.pos)
        await p.play(0, 60, 32, 100, 1 / 6)


n = 50


async def track(p: Track):
    p.new(trick, "three")
    while True:
        logger.log("4th: {0}", p.pos)
        await p.play(0, n, 24, 100, 1 / 6)
        # pos = await p.play(0, n, 23.5, 100, 1/12)
        # logger.log("wait: {0}", pos)
        # pos = await p.wait(24)


if __name__ == "__main__":
    # Bitwig sync: +38ms
    run(track, 120)
