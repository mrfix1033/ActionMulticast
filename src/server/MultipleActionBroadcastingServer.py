import asyncio
import socket
import sys
import traceback

import screeninfo
from aioconsole import ainput

from src.core.Exceptions import LastReleaseAlreadyInstalled
from src.core.Updater import Updater
from src.core.protocol.Keyboard import *
from src.core.protocol.Mouse import *
from src.core.protocol.ServerBroadcast import IAmServer
from src.core.utils.PacketUtils import PacketBuffer
from src.server import config


class MultipleActionBroadcastingServer:
    def __init__(self):
        self.version = "beta-3"
        self.updater = Updater(self.version, False)
        self.running = True
        self.clients: list[socket.socket] = []
        self.commands_buffer = PacketBuffer()
        self.server = None
        self.server_udp = None

    async def main(self):
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        self.start_listen_actions()
        tasks = [
            asyncio.create_task(self.updater.check_update()),
            asyncio.create_task(self.start_handle_input()),
            asyncio.create_task(self.start_server_broadcasting()),
            asyncio.create_task(self.start_server())
        ]

        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            pass

    async def update(self):
        try:
            self.updater.update()
        except LastReleaseAlreadyInstalled:
            print("Нет обновлений")

    async def start_server_broadcasting(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as self.server_udp:
            self.server_udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.server_udp.bind((config.ip, config.port))
            while self.running:
                self.server_udp.sendto(IAmServer().serialize() + b'\n', ("255.255.255.255", config.beacon_port))
                await asyncio.sleep(config.beacon_interval)

    async def start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.server:
            self.server.bind((config.ip, config.port))
            self.server.listen(1000)
            while self.running:
                try:
                    await self.accept_client()
                except socket.timeout:
                    continue
                except:
                    if self.running:
                        traceback.print_exc()

    async def accept_client(self):
        client_socket, client_address = await asyncio.get_event_loop().sock_accept(self.server)
        self.clients.append(client_socket)
        print("Connected {}".format(client_address))

    async def stop(self):
        print("Завершение работы...")
        self.running = False
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        for task in asyncio.all_tasks():
            if task is not asyncio.current_task():
                task.cancel()
        self.stop_listen_actions()

    async def start_handle_input(self):
        while self.running:
            try:
                command = await ainput("Вы можете вводить команды\n")
                if command == "update":
                    await self.update()
                elif command == "stop":
                    await self.stop()
                else:
                    print("Unknown command")
            except (KeyboardInterrupt, EOFError, asyncio.CancelledError):
                pass
            except:
                traceback.print_exc()

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
    while True:
        server = MultipleActionBroadcastingServer()
        loop = asyncio.get_event_loop()

        try:
            loop.run_until_complete(server.main())
        except KeyboardInterrupt:
            loop.run_until_complete(server.stop())
            break
        finally:
            loop.close()
