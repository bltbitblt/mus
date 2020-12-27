from rtmus import Track, note as n, run
from rtmus.log import logger
from rtmus.overlay import _a_a

acc = _a_a(0.7, 1, scale=0.5)


async def glitch(p: Track):
    p.r.seed(7)
    while True:
        inst = p.r.randint(1, 5)
        c = p.r.choice((0, 0, 0, 0, 12))
        await p.play((inst, n.C2 + c), p.r.choice((16, 8, 8, 8)))


async def drums(p: Track):
    hh = n.Ab1
    sn = n.Db1
    while True:
        await p.play(hh, 8, acc[p.pos])
        await p.play(hh, 8, acc[p.pos])
        await p.play((sn, hh), 8, acc[p.pos])
        await p.play(hh, 8, acc[p.pos])
        await p.play(hh, 8, acc[p.pos])
        await p.play(hh, 8, acc[p.pos])
        await p.play((sn, hh), 8, acc[p.pos])
        await p.play(hh, 8, acc[p.pos])


async def track(p: Track):
    g = None
    p.new(drums, 1, "drums")
    while True:
        p.sync()
        g = p.new(glitch, 0, "glitch", g)
        await p.wait(1)


if __name__ == "__main__":
    run(track, 110)
