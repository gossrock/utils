import asyncio
import random

data = []

async def generate_data():
    while True:
        await asyncio.sleep(1)
        num = random.randint(0,1000)
        data.append(num)

async def get_data():
    item_pointer = 0
    while True:
        await asyncio.sleep(0.1)
        if len(data) > item_pointer:
            yield data[item_pointer]
            item_pointer += 1


async def display_data():
    async for d in get_data():
        print(d)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(generate_data())
    asyncio.ensure_future(display_data())
    loop.run_forever()
