from rtmus import Track, note as n, run
from rtmus.log import logger
from rtmus.overlay import _a_a
from rtmus.scale import minor
from rtmus.util import note_to_name

acc = _a_a(0.5, 1)


async def trick(p: Track):
    while True:
        logger.log("three: {0}", p.pos)
        await p.play(60, 3)


async def track(p: Track):
    p.decay = 1 / 6

    # t = p.new(trick, name="three")
    # t.decay = 1 / 6
    while True:
        p.sync()
        for i in range(15):
            logger.log("4th: {0}", p.pos)
            vol = acc[p.pos]
            note = minor[i] + n.A2
            logger.log(note_to_name(note))
            await p.play(note, 8, vol)


if __name__ == "__main__":
    # Bitwig sync: +38ms
    run(track, 120)
