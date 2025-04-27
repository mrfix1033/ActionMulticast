import asyncio
import threading
import time
import traceback

import screeninfo

import src.core.utils.CommandsListener
from src.core.CoreCommands import *
from src.core.Exceptions import LastReleaseAlreadyInstalled
from src.core.Updater import Updater
from src.core.protocol.Keyboard import *
from src.core.protocol.Mouse import *
from src.core.protocol.ServerBroadcast import IAmServer
from src.core.utils.PacketUtils import PacketBuffer
from src.server import config
from src.server.commands import *


class ActionMulticastServer:
    def __init__(self):
        self.version = CoreConstants.version
        self.updater = Updater(self.version, False)
        self.commands_buffer = PacketBuffer()
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
            print("Крепление к потоку", thread)
            thread.join()

    def update(self):
        try:
            self.updater.update()
        except LastReleaseAlreadyInstalled:
            print("Нет обновлений")

    def start_handle_input(self):
        commands_map = {
            'startup': StartupCommand(),
            'update': UpdateCommand(self.update),
            'restart': RestartCommand(None, self.restart, None, None),
            'stop': StopCommand(None, self.stop, None, None),
            'version': Version(self.version),
        }
        commands_map["help"] = HelpCommand(list(commands_map.values()))
        src.core.utils.CommandsListener.start_listen_commands(commands_map, lambda: self.running)
        print("Обработка команд прекращена")

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
        print("Завершение работы...")
        self.stop_logic()
        print("Ожидание завершения работы...")

    def restart(self):
        print("Перезапуск...")
        self.stop_logic()

    async def start_server_broadcasting(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as self.server_udp:
            self.server_udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.server_udp.bind((config.ip, config.port))
            print("Маячковый сервер запущен")
            while self.running:
                self.server_udp.sendto(IAmServer().serialize() + b'\n', ("255.255.255.255", config.beacon_port))
                await asyncio.sleep(config.beacon_interval)
        print("Маячковый сервер остановлен")

    async def start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.server:
            self.server.bind((config.ip, config.port))
            self.server.listen(1000)
            print("Основной сервер запущен")
            while self.running:
                try:
                    await self.accept_client()
                except InterruptedError:
                    continue
                except:
                    if self.running:
                        traceback.print_exc()
                        self.server.accept()
        print("Основной сервер остановлен")

    async def accept_client(self):
        client_socket, client_address = self.server.accept()
        self.clients.append(client_socket)
        print("Connected {}".format(client_address))

    def send_to_all_clients(self, data: bytes):
        data += '\n'.encode()
        for i in range(len(self.clients) - 1, -1, -1):
            client_socket = self.clients[i]
            try:
                client_socket.send(data)
            except ConnectionError:
                self.clients.pop(i)

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
            self.send_to_all_clients(KeyboardPressAction(key.vk).serialize())

        def on_release(key):
            if isinstance(key, keyboard.Key):
                key = key.value
            self.send_to_all_clients(KeyboardReleaseAction(key.vk).serialize())

        listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        listener.start()
        return listener

    def run_mouse_listener(self):
        from pynput import mouse
        monitor = screeninfo.get_monitors()[0]
        screen_width, screen_height = monitor.width, monitor.height

        def on_move(x, y):
            self.send_to_all_clients(
                MouseMovementAbsolutePercentageAction(x / screen_width, y / screen_height).serialize())

        def on_click(x, y, magic_button, pressed):
            magic_to_button_index = {(4, 2, 0): 1, (64, 32, 0): 2, (16, 8, 0): 3}
            button = magic_to_button_index.get(magic_button.value)
            if button is None:
                print("unknown mouse button pressed/released: {}".format(magic_button))
                return
            if pressed:
                self.send_to_all_clients(MousePressAction(button).serialize())
            else:
                self.send_to_all_clients(MouseReleaseAction(button).serialize())

        def on_scroll(x, y, dx, dy):
            self.send_to_all_clients(MouseScrollAction(dx, dy).serialize())

        listener = mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)
        listener.start()
        return listener


if __name__ == "__main__":
    print(CoreConstants.greeting("Server"))
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
            print("КРИТИЧЕСКАЯ ОШИБКА, пожалуйста, напишите автору")
            traceback.print_exc()
            print("Рестарт через 5 секунд...")
            time.sleep(5)
