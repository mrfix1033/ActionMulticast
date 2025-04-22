import json
import aiohttp

from src.core import AsyncUtils


class Updater:
    def __init__(self, version):
        self.version = version
        self.release = None
        AsyncUtils.start_thread_async_task(self.check_update())

    async def check_update(self):
        """
        :return: None - если установлена последняя версия, dict (release) - если есть версия новее
        """
        url_releases = "https://api.github.com/repos/mrfix1033/multipleactionbroadcasting/releases"
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url_releases) as response:
                text = await response.text()
        last_release = json.loads(text)[-1]
        if not last_release["draft"] \
                and not last_release["prerelease"] \
                and last_release["name"] != self.version:
            self.release = last_release
            self.notify()

    def notify(self):
        print("Доступна новая версия программы (текущая: {}) (новая: {})".format(self.version, self.release["name"]))
