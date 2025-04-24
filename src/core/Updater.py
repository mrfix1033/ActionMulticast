import json
import sys

import aiohttp

from src.core.Exceptions import LastReleaseAlreadyInstalled


class Updater:
    def __init__(self, version, is_client: bool):
        self.version = version
        self.release = None
        self.is_client = is_client

    async def check_update(self):
        """
        :return: None - если установлена последняя версия, dict (release) - если есть версия новее
        """
        url_releases = "http://api.github.com/repos/mrfix1033/multipleactionbroadcasting/releases"
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url_releases) as response:
                text = await response.text()
        last_release = json.loads(text)[-1]
        if not last_release["draft"] \
                and not last_release["prerelease"] \
                and last_release["tag_name"] != self.version:
            self.release = last_release
            self.notify()

    def notify(self):
        print(
            "Доступна новая версия программы (текущая: {}) (новая: {}), напишите update для обновления".format(self.version, self.release["tag_name"]))

    def update(self):
        if self.release is None:
            raise LastReleaseAlreadyInstalled()
        client_or_server = "client" if self.is_client else "server"
        platform_to_extension = {"win32": ".exe"}
        release_version = self.release["tag_name"]
        need_version = f"MultipleActionBroadcasting-{client_or_server}-{release_version}-{sys.platform}{platform_to_extension[sys.platform]}"
        for asset in self.release["assets"]:
            if asset["name"] == need_version:
                download_url = asset["browser_download_url"]
                # async with aiohttp.ClientSession() as session:
                #     async with session.stream()

