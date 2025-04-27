import abc
import sys
import typing
import winreg

from src.core import CoreConstants
from src.core.Loging import Logger
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


class StartupCommand(BaseCommand):
    def get_usage(self) -> str:
        return "startup add/remove - добавить/убрать программу из автозагрузки"

    def execute(self, args: list[str]):
        if len(args) < 1:
            not_enough_arguments(self.get_usage())
            return
        action = args[0]
        if action == "add":
            self._add_to_startup()
        elif action == "remove":
            self._remove_from_startup()
        else:
            incorrect_usage(self.get_usage())
            return

    def _add_to_startup(self):
        raise NotImplementedError("Ещё не готово")
        app_name = CoreConstants.program_name
        exe_path = sys.executable if getattr(sys, 'frozen', False) else sys.argv[0]
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    key_path,
                    0, winreg.KEY_SET_VALUE
            ) as key:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{exe_path}"')
            Logger.log(f"Программа добавлена в автозагрузку")
        except:
            Logger.log("Ошибка добавления в автозагрузку")
            traceback.print_exc()

    def _remove_from_startup(self):
        raise NotImplementedError("Ещё не готово")
        try:
            with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0, winreg.KEY_SET_VALUE
            ) as key:
                winreg.DeleteValue(key, name)
            Logger.log(f"Программа удалена из автозагрузки")
        except:
            Logger.log("Ошибка удаления из автозагрузки")
            traceback.print_exc()


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
