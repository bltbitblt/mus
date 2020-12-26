from rtmus import Track, run
from rtmus.log import logger
from rtmus.overlay import _a_a

acc = _a_a(0.5, 1)


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
        logger.log("4th: {0}", p.pos)
        # await p.wait(4)
        p.cc(p.c.MODULATION_WHEEL, p.r.random())
        vol = acc[p.pos]
        await p.play((50, 54), 4, vol)


if __name__ == "__main__":
    # Bitwig sync: +38ms
    run(track, 120)
