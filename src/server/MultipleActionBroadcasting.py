import asyncio
import socket
import sys
import typing

import screeninfo

from src.core import AsyncUtils
from src.core.protocol.Keyboard import *
from src.core.protocol.Mouse import *
from src.server import config
from src.core.Updater import Updater


class MultipleActionBroadcasting:
    def __init__(self):
        asyncio.run(self.main())

    async def main(self):
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        self.version = "beta-2"
        self.updater = Updater(self.version)
        self.threads = []
        self.running = True
        self.clients: list[socket.socket] = []

        self.threads.append(AsyncUtils.start_thread_async_task(self.start_handle_input()))
        self.threads.append(AsyncUtils.start_thread_async_task(self.start_listen_actions()))
        await self.start_server()

    async def start_server(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((config.ip, config.port))
        self.server.listen(1000)
        while self.running:
            await self.accept_client()

    async def accept_client(self):
        client_socket, client_address = self.server.accept()
        self.clients.append(client_socket)
        print("Connected {}".format(client_address))
        # asyncio.create_task(self.client_life(server, client_socket))

    # async def client_life(self, server, client):
    #     while True:
    #         await asyncio.sleep(0.1)

    async def start_handle_input(self):
        while self.running:
            command = input("> ")
            if command == "stop":
                self.running = False
            else:
                print("Unknown command")

    async def start_listen_actions(self):
        AsyncUtils.start_thread_async_task(self.keyboard_listening())
        AsyncUtils.start_thread_async_task(self.mouse_listening())

    async def keyboard_listening(self):
        from pynput import keyboard
        def on_press(key):
            if isinstance(key, keyboard.Key):
                key = key.value
            self.send_to_all_clients(KeyboardPressAction(key.vk).serialize())

        def on_release(key):
            if isinstance(key, keyboard.Key):
                key = key.value
            self.send_to_all_clients(KeyboardReleaseAction(key.vk).serialize())

        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()

    async def mouse_listening(self):
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

        with mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll) as listener:
            listener.join()

    def send_to_all_clients(self, data: bytes):
        data += '\n'.encode()
        for i in range(len(self.clients) - 1, -1, -1):
            client_socket = self.clients[i]
            try:
                client_socket.send(data)
            except ConnectionError:
                self.clients.pop(i)


if __name__ == "__main__":
    MultipleActionBroadcasting()
