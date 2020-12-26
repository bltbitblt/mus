from rtmus import Track, run
from rtmus.log import logger


async def trick(p: Track):
    while True:
        logger.log("three: {0}", p.pos)
        await p.play(60, 3)


n = 50


async def track(p: Track):
    p.decay = 1 / 6

    # t = p.new(trick, name="three")
    # t.decay = 1 / 6
    while True:
        p.sync()
        # p.cc(p.c.MODULATION_WHEEL, p.r.random())
        logger.log("4th: {0}", p.pos)
        # await p.wait(4)
        p.on(50)
        await p.wait(4)
        p.on(54)
        await p.wait(4)
        p.on(58)
        await p.wait(4)
        p.off_all()
        await p.wait(4)


if __name__ == "__main__":
    # Bitwig sync: +38ms
    run(track, 120)
