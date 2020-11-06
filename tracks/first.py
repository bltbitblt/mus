import asyncio

from rtmus import Performance, run


async def track(p: Performance):
    try:
        while True:
            await p.metronome.bar.wait()
            await p.play(0, 48, 24, 100)
            await p.play(0, 48, 24, 100)
            await p.play(0, 48, 24, 100)
            await p.play(0, 48, 12, 100)
            print("beat")
    except asyncio.CancelledError:
        print("track stop")
    pass


if __name__ == "__main__":
    run(track)
