from rtmus import Track, note as n, run
from rtmus.overlay import _a_a
from rtmus.util import cyc

acc = _a_a(0.7, 1, scale=0.5)


async def glitch(p: Track):
    p.r.seed(7)
    while True:
        inst = p.r.randint(1, 5)
        c = p.r.choice((0, 0, 0, 0, 12))
        await p.play((inst, n.C2 + c), p.r.choice((16, 8, 8, 8)))


async def drums(p: Track):
    hh_c = n.Ab1
    hh_o = n.Eb1
    hh = cyc([hh_c, hh_c, hh_c, hh_c, hh_o])
    sn = n.Db1
    while True:
        p.sync()
        await p.play(hh(), 8, p.get(acc))
        await p.play(hh(), 8, p.get(acc))
        await p.play((sn, hh()), 8, p.get(acc))
        await p.play(hh(), 8, p.get(acc))
        await p.play(hh(), 8, p.get(acc))
        await p.play(hh(), 8, p.get(acc))
        await p.play((sn, hh()), 8, p.get(acc))
        await p.play(hh(), 8, p.get(acc))


async def track(p: Track):
    g = None
    d = None
    while True:
        p.sync()
        d = p.new(drums, 1, "drums", d)
        g = p.new(glitch, 0, "glitch", g)
        await p.wait(-2)


if __name__ == "__main__":
    run(track, 110)
