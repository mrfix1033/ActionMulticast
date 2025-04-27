import socket
from abc import ABC

from src.core.CoreCommands import BaseCommand
from src.core.Loging import Logger
from src.core.utils import CommandsUtils


class ServerToClientCommand(BaseCommand, ABC):
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
                ip_addr = socket.inet_aton(args[0])
            except socket.error:
                Logger.log(CommandsUtils.incorrect_usage(self.get_usage()))
                return
            self.ip_func(ip_addr)
            self.all_clients_func()


class RestartCommand(ServerToClientCommand):
    def get_usage(self) -> str:
        return "restart <IP>/server/all_clients/all - перезапустить программу на: определённом компьютере/сервере(здесь)/всех клиентах/везде"


class StopCommand(ServerToClientCommand):
    def get_usage(self) -> str:
        return "stop <IP>/server/all_clients/all - остановить программу на: определённом компьютере/сервере(здесь)/всех клиентах/везде"
