import asyncio
import subprocess
import sys
import threading
import time
import traceback

import screeninfo

import src.core.utils.CommandsListener
from src.core import CoreConstants
from src.core.CoreCommands import *
from src.core.Exceptions import LastReleaseAlreadyInstalled
from src.core.Updater import Updater
from src.core.protocol.FromServer import ClientsConsoleVisiblePacket, UpdateClientPacket, StartupPacket
from src.core.protocol.Keyboard import *
from src.core.protocol.Mouse import *
from src.core.protocol.ServerBroadcast import IAmServer
from src.core.utils.PacketUtils import PacketBuilder
from src.server import config
from src.server.commands import *


class ActionMulticastServer:
    def __init__(self):
        self.version = CoreConstants.version
        self.updater = Updater(self.version, False)
        self.commands_buffer = PacketBuilder()
        self.running = True

        self.threads = []
        self.clients: list[socket.socket] = []
        self.server = None
        self.server_udp = None

    def main(self):
        self.threads = [
            threading.Thread(target=self.start_handle_input),
            threading.Thread(target=self.updater.check_update),
            threading.Thread(target=lambda: asyncio.run(self.start_server())),
            threading.Thread(target=lambda: asyncio.run(self.start_server_broadcasting())),
        ]
        for thread in self.threads:
            thread.start()
        self.start_listen_actions()

    async def _async_start(self):
        await asyncio.gather(
            self.start_server(),
            self.start_server_broadcasting(),
        )

    def join(self):
        for thread in self.threads:
            Logger.log("Крепление к потоку", thread)
            thread.join()
        Logger.log("Все потоки завершены")

    def update(self):
        try:
            self.updater.update()
        except LastReleaseAlreadyInstalled:
            Logger.log("Нет обновлений")

    def start_handle_input(self):
        commands_map = {
            "startup": StartupCommand(self.clients_startup),
            "update": UpdateCommand(self.update),
            "clients_console": ClientsConsole(lambda: self.send_to_all_clients(ClientsConsoleVisiblePacket(False)),
                                              lambda: self.send_to_all_clients(ClientsConsoleVisiblePacket(True))),
            "update_all_clients": UpdateAllClients(self.update_all_clients),
            "count": Count(lambda: len(self.clients)),
            "restart": RestartCommand(None, self.restart, None, None),
            "stop": StopCommand(None, self.stop, None, None),
            "version": Version(self.version),
        }
        commands_map["help"] = HelpCommand(list(commands_map.values()))
        src.core.utils.CommandsListener.start_listen_commands(commands_map, lambda: self.running)
        Logger.log("Обработка команд прекращена")

    def stop_logic(self):
        self.running = False
        global is_main_loop_running
        is_main_loop_running = False

        self.stop_listen_actions()

        for client in self.clients:
            try:
                client.close()
            except:
                pass

        if self.server is not None:
            self.server.close()
        if self.server_udp is not None:
            self.server_udp.close()

    def stop(self):
        Logger.log("Завершение работы...")
        self.stop_logic()
        Logger.log("Ожидание завершения работы...")

    def restart(self):
        Logger.log("Перезапуск...")
        self.stop_logic()
        Logger.log("Ожидание завершения работы...")
        python = sys.executable
        Logger.log("Запуск нового процесса...")
        subprocess.Popen([python] + sys.argv)
        Logger.log("Новый процесс запущен")
        while True:  # чтобы не завершать текущий процесс (избежать ошибки)
            time.sleep(999999)

    async def start_server_broadcasting(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as self.server_udp:
                self.server_udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                self.server_udp.bind((config.ip, config.port))
                Logger.log("Маячковый сервер запущен")
                while self.running:
                    self.server_udp.sendto(IAmServer.get_id().encode() + b' 0 ', ("255.255.255.255", config.beacon_port))
                    await asyncio.sleep(config.beacon_interval)
        finally:
            Logger.log("Маячковый сервер остановлен")

    async def start_server(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.server:
                self.server.bind((config.ip, config.port))
                self.server.listen(1000)
                Logger.log("Основной сервер запущен")
                while self.running:
                    try:
                        await self.accept_client()
                    except InterruptedError:
                        continue
                    except:
                        if self.running:
                            traceback.print_exc()
                            self.server.accept()
        finally:
            Logger.log("Основной сервер остановлен")

    async def accept_client(self):
        client_socket, client_address = self.server.accept()
        self.clients.append(client_socket)
        Logger.log(f"{len(self.clients)}) Подключен {client_address}")

    def send_to_all_clients(self, packet: Packet):
        packet_bytes = packet.serialize()
        packet_data = f"{packet.get_id()} {len(packet_bytes)} ".encode() + packet_bytes
        for i in range(len(self.clients) - 1, -1, -1):
            client_socket = self.clients[i]
            try:
                client_socket.send(packet_data)
            except ConnectionError:
                Logger.log(f"{len(self.clients) - 1}) Отключен {self.clients.pop(i).getpeername()}")

    def start_listen_actions(self):
        self.keyboard_listener = self.run_keyboard_listener()
        self.mouse_listener = self.run_mouse_listener()

    def stop_listen_actions(self):
        self.keyboard_listener.stop()
        self.mouse_listener.stop()

    def run_keyboard_listener(self):
        from pynput import keyboard
        def on_press(key):
            if isinstance(key, keyboard.Key):
                key = key.value
            self.send_to_all_clients(KeyboardPressPacket(key.vk))

        def on_release(key):
            if isinstance(key, keyboard.Key):
                key = key.value
            self.send_to_all_clients(KeyboardReleasePacket(key.vk))

        listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        listener.start()
        return listener

    def run_mouse_listener(self):
        from pynput import mouse
        monitor = screeninfo.get_monitors()[0]
        screen_width, screen_height = monitor.width, monitor.height

        def on_move(x, y):
            self.send_to_all_clients(
                MouseMovementAbsolutePercentagePacket(x / screen_width, y / screen_height))

        def on_click(x, y, magic_button, pressed):
            magic_to_button_index = {(4, 2, 0): 1, (64, 32, 0): 2, (16, 8, 0): 3}
            button = magic_to_button_index.get(magic_button.value)
            if button is None:
                Logger.log("unknown mouse button pressed/released: {}".format(magic_button))
                return
            if pressed:
                self.send_to_all_clients(MousePressPacket(button))
            else:
                self.send_to_all_clients(MouseReleasePacket(button))

        def on_scroll(x, y, dx, dy):
            self.send_to_all_clients(MouseScrollPacket(dx, dy))

        listener = mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)
        listener.start()
        return listener

    def update_all_clients(self, path_to_file):
        with open(path_to_file, 'rb') as file:
            self.send_to_all_clients(UpdateClientPacket(file.read()))

    def clients_startup(self, is_add):
        self.send_to_all_clients(StartupPacket(is_add))

if __name__ == "__main__":
    Logger.log(CoreConstants.greeting("Server"))
    is_main_loop_running = True
    while is_main_loop_running:
        server = ActionMulticastServer()
        try:
            server.main()
            server.join()
        except KeyboardInterrupt:
            server.stop()
            server.join()
            break
        except:
            Logger.log("КРИТИЧЕСКАЯ ОШИБКА, пожалуйста, напишите автору")
            traceback.print_exc()
            Logger.log("Рестарт через 5 секунд...")
            time.sleep(5)
    Logger.log("Выполнение программы завершено")
