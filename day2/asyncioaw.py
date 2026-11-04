import time
import asyncio

def say_hello():
    print("Hello")
    time.sleep(2)
    print("World")

say_hello()


async def say_hello():
    print("Hello")

    await asyncio.sleep(2)

    print("World")

asyncio.run(say_hello())

# async def task(name, delay):
#     print(f"{name} started")

#     await asyncio.sleep(delay)

#     print(f"{name} completed")

# async def main():

#     start = time.perf_counter()

#     await task("Task A", 2)
#     await task("Task B", 2)
#     await task("Task C", 2)

#     print(time.perf_counter() - start)

# asyncio.run(main())


async def task(name, delay):

    print(f"{name} started")

    await asyncio.sleep(delay)

    print(f"{name} completed")

async def main():

    start = time.perf_counter()

    await asyncio.gather(
        task("Task A", 2),
        task("Task B", 2),
        task("Task C", 2)
    )

    print(time.perf_counter() - start)

asyncio.run(main())