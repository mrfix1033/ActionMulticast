import asyncio
import socket
import sys

import screeninfo
import win32api
import win32con

from src.client import config
from src.core import AsyncUtils
from src.core.Updater import Updater
from src.core.protocol.Keyboard import *
from src.core.protocol.Mouse import *


class MultipleActionBroadcasting:
    def __init__(self):
        asyncio.run(self.main())

    async def main(self):
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        self.version = "beta-2"
        self.updater = Updater(self.version)
        monitor = screeninfo.get_monitors()[0]
        self.screen_width, self.screen_height = monitor.width, monitor.height

        AsyncUtils.start_thread_async_task(self.start_handle_input())
        await self.start_client()

    async def start_client(self):
        self.running = True

        while self.running:
            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect((config.server_ip, config.server_port))
            except ConnectionRefusedError:
                print("Connection refused")
                await asyncio.sleep(5)
                continue
            print("Connected")
            await self.listen(client)

    async def listen(self, client):
        while True:
            try:
                data = client.recv(1024)
            except ConnectionResetError:
                print("Connection reset")
                break
            commands = data.decode().split('\n')
            for command in commands:
                if not command:
                    break
                await self.handle(command)

    async def handle(self, text):
        text = text.split(' ')
        print(text)
        protocol_name, protocol_data = text[0], text[1:]
        if protocol_name == KeyboardPressAction.get_id():
            protocol = KeyboardPressAction.deserialize(protocol_data)
            win32api.keybd_event(protocol.c, 0, 0, 0)
        elif protocol_name == KeyboardReleaseAction.get_id():
            protocol = KeyboardReleaseAction.deserialize(protocol_data)
            win32api.keybd_event(protocol.c, 0, win32con.KEYEVENTF_KEYUP, 0)
        elif protocol_name == MouseMovementAbsolutePercentageAction.get_id():
            protocol = MouseMovementAbsolutePercentageAction.deserialize(protocol_data)
            print(int(protocol.x * self.screen_width))
            # win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, int(protocol.x * self.screen_width), int(protocol.y * self.screen_height), win32con.MOUSEEVENTF_ABSOLUTE)
        elif protocol_name == MousePressAction.get_id():
            protocol = MousePressAction.deserialize(protocol_data)
            if protocol.b == 1:
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
            elif protocol.b == 2:
                win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEDOWN, 0, 0)
            elif protocol.b == 3:
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0)
            else:
                print("unknown mouse button pressed")
        elif protocol_name == MouseReleaseAction.get_id():
            protocol = MouseReleaseAction.deserialize(protocol_data)
            if protocol.b == 1:
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
            elif protocol.b == 2:
                win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEUP, 0, 0)
            elif protocol.b == 3:
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0)
            else:
                print("unknown mouse button pressed")
        elif protocol_name == MouseScrollAction.get_id():
            protocol = MouseScrollAction.deserialize(protocol_data)
            win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, protocol.dx, protocol.dy)
        else:
            print("unknown protocol name {}".format(protocol_name))

    async def start_handle_input(self):
        while True:
            command = input("> ")
            if command == "stop":
                self.running = False
            else:
                print("Unknown command")


if __name__ == "__main__":
    MultipleActionBroadcasting()
