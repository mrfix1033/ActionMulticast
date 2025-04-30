import socket
import typing
from abc import ABC

from src.core.CoreCommands import BaseCommand
from src.core.Loging import Logger
from src.core.utils import CommandsUtils, StartupUtils, StringUtils
from src.core.utils.CommandsUtils import not_enough_arguments, incorrect_usage
from src.server.ClientUtils import UpdateAllClientsData


class ShutdownCommand(BaseCommand, ABC):
    def __init__(self, ip_func, server_func, all_clients_func, all_func):
        self.ip_func = ip_func
        self.server_func = server_func
        self.all_clients_func = all_clients_func
        self.all_func = all_func

    def execute(self, args: list[str]):
        if not args:
            CommandsUtils.not_enough_arguments(self.get_usage())
            return
        if args[0] == "all":
            self.all_func()
        elif args[0] == "all_clients":
            self.all_clients_func()
        elif args[0] == "server":
            self.server_func()
        else:
            try:
                socket.inet_aton(args[0])
            except socket.error:
                Logger.log(CommandsUtils.incorrect_usage(self.get_usage()))
                return
            self.ip_func(args[0])


class RestartCommand(ShutdownCommand):
    def get_usage(self) -> str:
        return "restart <IP>/server/all_clients/all - перезапустить программу на: определённом компьютере/сервере(здесь)/всех клиентах/везде (потеряете 20МБ ОЗУ, также можно перезагрузить пк)"


class StopCommand(ShutdownCommand):
    def get_usage(self) -> str:
        return "stop <IP>/server/all_clients/all - остановить программу на: определённом компьютере/сервере(здесь)/всех клиентах/везде"


class ClientsConsole(BaseCommand):
    def __init__(self, func_to_hide: typing.Callable, func_to_show: typing.Callable):
        self.func_to_hide = func_to_hide
        self.func_to_show = func_to_show

    def get_usage(self) -> str:
        return "clients_console hide/show - скрыть/показать консоль у всех клиентов"

    def execute(self, args: list[str]):
        if not args:
            not_enough_arguments(self.get_usage())
            return
        if args[0] == "hide":
            self.func_to_hide()
            Logger.log("Консоль у клиентов скрыта")
        elif args[0] == "show":
            Logger.log("Консоль у клиентов открыта")
            self.func_to_show()
        else:
            incorrect_usage(self.get_usage())


class UpdateAllClients(BaseCommand):
    def __init__(self, func_to_update: typing.Callable[[str], None]):
        self.func_to_update = func_to_update

    def get_usage(self) -> str:
        return "update_all_clients <путь к файлу> - отправляет file всем клиентам, они обновляются (но не перезапускаются)"

    def execute(self, args: list[str]):
        if not args:
            not_enough_arguments(self.get_usage())
            return
        path_to_file = StringUtils.to_str_and_join(*args).strip("\"'")
        Logger.log("Начата рассылка...")
        self.func_to_update(path_to_file)
        Logger.log("Рассылка окончена")


class Count(BaseCommand):
    def __init__(self, func_to_get_count: typing.Callable[[], int]):
        self.func_to_get_count = func_to_get_count

    def get_usage(self) -> str:
        return "count - выводит количество подключенных клиентов"

    def execute(self, args: list[str]):
        Logger.log(self.func_to_get_count())


class StartupCommand(BaseCommand):
    """
    @:param func_for_client - в функцию передается флаг (добавлять в автозагрузку?), если False, то нужно убрать
    """

    def __init__(self, func_for_client: typing.Callable[[bool], None]):
        self.func_for_client = func_for_client

    def get_usage(self) -> str:
        return "startup add/remove clients/server - добавить/убрать клиентам/серверу программу из автозагрузки"

    def execute(self, args: list[str]):
        if len(args) != 2:
            not_enough_arguments(self.get_usage())
            return
        action, whom = args
        if whom == "server":
            if action == "add":
                StartupUtils.add_to_startup("Server")
                Logger.log(f"Программа добавлена в автозагрузку")
            elif action == "remove":
                StartupUtils.remove_from_startup("Server")
                Logger.log("Программа удалена из автозагрузки")
            else:
                incorrect_usage(self.get_usage())
        elif whom == "clients":
            if action == "add":
                self.func_for_client(True)
                Logger.log("Клиентам отправлена команда добавить приложение в автозагрузку")
            elif action == "remove":
                self.func_for_client(False)
                Logger.log("Клиентам отправлена команда убрать приложение из автозагрузки")
            else:
                incorrect_usage(self.get_usage())
        else:
            incorrect_usage(self.get_usage())
            return


class UpdateAllClientsInfo(BaseCommand):
    def __init__(self, data_getter: typing.Callable[[], UpdateAllClientsData]):
        self.data_getter = data_getter

    def get_usage(self) -> str:
        return "update_all_clients_info - показывает статистику по обновлению всех клиентов"

    def execute(self, args: list[str]):
        data = self.data_getter()
        if data is None:
            Logger.log("Команда обновления не вызывалась")
            return
        Logger.log(f"Обновленные ({len(data.updated_ips)}):", StringUtils.to_str_and_join(*data.updated_ips))
        Logger.log(f"Ошибка обновления ({len(data.failed_ips)}):", StringUtils.to_str_and_join(*data.failed_ips))
        unknown_ips = data.client_ips.copy()
        for ip in data.failed_ips + data.updated_ips:
            unknown_ips.remove(ip)
        Logger.log(f"Неизвестно ({len(unknown_ips)}):", StringUtils.to_str_and_join(*unknown_ips))
        Logger.log("Всего:", len(data.client_ips))
