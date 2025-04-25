import typing
from src.core.CoreCommands import BaseCommand

class RestartCommand(BaseCommand):
    def __init__(self, restart_func: typing.Callable):
        self.restart_func = restart_func

    def get_usage(self) -> str:
        return "restart - перезапустить программу"

    async def execute(self, args: list[str]):
        self.restart_func()


class StopCommand(BaseCommand):
    def __init__(self, stop_func: typing.Callable):
        self.stop_func = stop_func

    def get_usage(self) -> str:
        return "stop - остановить программу"

    async def execute(self, args: list[str]):
        self.stop_func()
