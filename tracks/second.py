from rtmus import Track, note as n, run
from rtmus.log import logger
from rtmus.overlay import _a_a
from rtmus.scale import minor
from rtmus.util import note_to_name


async def glitch(p: Track):
    while True:
        await p.play(n.C3, 8)


async def track(p: Track):
    g = None
    while True:
        p.sync()
        g = p.new(glitch, 0, "glitch", g)
        await p.wait(-2)


if __name__ == "__main__":
    run(track, 80)
