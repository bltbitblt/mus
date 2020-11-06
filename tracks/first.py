import asyncio

from rtmus import run


async def track(performance):
    try:
        print("start")
        while True:
            await performance.wait(24)
            print("beat")
    except asyncio.CancelledError:
        print("stop")
    pass


if __name__ == "__main__":
    run(track)
