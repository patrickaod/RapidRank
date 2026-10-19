import asyncio


async def main():
    queue = asyncio.Queue()

    await queue.put(1234)
    await queue.put(5678)
    await queue.put(9012)

    while not queue.empty():
        discord_id = await queue.get()
        print("Processing user:", discord_id)
        queue.task_done()


asyncio.run(main())