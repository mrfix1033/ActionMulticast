import abc
import typing

from src.core.utils.CommandsUtils import *


class BaseCommand(abc.ABC):
    @abc.abstractmethod
    def get_usage(self) -> str:
        pass

    @abc.abstractmethod
    def execute(self, args: list[str]):
        pass


class HelpCommand(BaseCommand):
    def __init__(self, commands: list[BaseCommand]):
        self.commands = commands

    def get_usage(self) -> str:
        return "help - показать все доступные команды"

    def execute(self, args: list[str]):
        for command in self.commands:
            Logger.log(command.get_usage())


class UpdateCommand(BaseCommand):
    def __init__(self, update_func):
        self.update_func = update_func

    def get_usage(self) -> str:
        return "update - обновить программу до последней версии"

    def execute(self, args: list[str]):
        self.update_func()


class Version(BaseCommand):
    def __init__(self, version):
        self.version = version

    def get_usage(self) -> str:
        return "version - посмотреть версию программы"

    def execute(self, args: list[str]):
        Logger.log(self.version)


class CheckUpdate(BaseCommand):
    def __init__(self, check_update_func: typing.Callable):
        self.check_update_func = check_update_func

    def get_usage(self) -> str:
        return "check_update - проверить наличие обновлений"

    def execute(self, args: list[str]):
        self.check_update_func()
