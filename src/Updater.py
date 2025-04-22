import asyncio
import sys

import aiohttp


def check_update():
    url_releases = "https://github.com/repos/mrfix1033/multipleactionbroadcasting/releases"
    version = "b1"

    async def check():
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url_releases) as response:
                text = await response.text()
                print(text)

    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check())
