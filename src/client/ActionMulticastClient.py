import asyncio
import atexit
import os
import socket
import subprocess
import time
import traceback

import win32api
import win32con

import src.core.utils.CommandsListener
from src.client import config
from src.client.commands import *
from src.core.CoreCommands import *
from src.core.Exceptions import LastReleaseAlreadyInstalled
from src.core.Updater import Updater
from src.core.protocol.Keyboard import *
from src.core.protocol.Mouse import *
from src.core.protocol.ServerBroadcast import IAmServer
from src.core.utils.PacketUtils import PacketBuffer


class ActionMulticastClient:
    def __init__(self):
        self.version = CoreConstants.version
        self.updater = Updater(self.version, True)
        self.commands_buffer = PacketBuffer()
        self.running = True

    async def main(self):
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        tasks = [
            asyncio.create_task(self.updater.check_update()),
            asyncio.create_task(self.start_handle_input()),
            asyncio.create_task(self.start_client())
        ]

        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            pass

    async def update(self):
        try:
            await self.updater.update()
        except LastReleaseAlreadyInstalled:
            print("Нет обновлений")

    async def start_handle_input(self):
        commands_map = {
            'startup': StartupCommand(),
            'update': UpdateCommand(lambda: asyncio.gather(asyncio.create_task(self.update()))),
            'restart': RestartCommand(lambda: asyncio.gather(asyncio.create_task(self.restart()))),
            'stop': StopCommand(lambda: asyncio.gather(asyncio.create_task(self.stop())))
        }
        commands_map["help"] = HelpCommand(list(commands_map.values()))
        await src.core.utils.CommandsListener.start_listen_commands(commands_map, lambda: self.running)

    async def stop_logic(self):
        self.running = False
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        global is_main_loop_running
        is_main_loop_running = False

    async def stop(self):
        print("Завершение работы...")
        await self.stop_logic()

    async def restart(self):
        print("Перезапуск...")
        await self.stop_logic()
        python = sys.executable
        script = os.path.abspath(sys.argv[0])
        subprocess.Popen([python, script] + sys.argv[1:])
        atexit._run_exitfuncs()
        os._exit(0)

    async def start_client(self):
        while self.running:
            server_ip_port = config.server_ip, config.server_port
            if server_ip_port[0] is None:
                print("Поиск серверов...")
                server_ip_port = await self.find_server()
            print(f"Подключение к {server_ip_port[0]}:{server_ip_port[1]}")
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
                    client.connect(server_ip_port)
                    print("Подключено")
                    await self.start_listen_server(client)
            except ConnectionRefusedError:
                print("Connection refused")
                await asyncio.sleep(5)
                continue
            except:
                traceback.print_exc()

    async def find_server(self) -> str:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_client:
            udp_client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            udp_client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            udp_client.bind(('0.0.0.0', config.beacon_port))
            udp_client.settimeout(0.1)

            command_buffer = PacketBuffer()
            is_server_found = False

            while self.running and not is_server_found:
                try:
                    data, ip_port = udp_client.recvfrom(1024)
                except socket.timeout:
                    await asyncio.sleep(0.5)
                    continue
                command_buffer.put(data.decode())
                commands = command_buffer.get()
                for command in commands:
                    command = command.split(' ')
                    if command[0] == IAmServer.get_id():
                        is_server_found = True
        return ip_port

    async def start_listen_server(self, client):
        while self.running:
            try:
                data = client.recv(1024)
            except ConnectionResetError:
                print("Connection reset")
                break
            self.commands_buffer.put(data.decode())
            for command in self.commands_buffer.get():
                await self.handle_command(command)

    async def handle_command(self, text):
        text = text.split(' ')
        protocol_name, protocol_data = text[0], text[1:]
        if protocol_name == KeyboardPressAction.get_id():
            protocol = KeyboardPressAction.deserialize(protocol_data)
            win32api.keybd_event(protocol.c, 0, 0, 0)
        elif protocol_name == KeyboardReleaseAction.get_id():
            protocol = KeyboardReleaseAction.deserialize(protocol_data)
            win32api.keybd_event(protocol.c, 0, win32con.KEYEVENTF_KEYUP, 0)
        elif protocol_name == MouseMovementAbsolutePercentageAction.get_id():
            protocol = MouseMovementAbsolutePercentageAction.deserialize(protocol_data)
            win32api.mouse_event(win32con.MOUSEEVENTF_MOVE | win32con.MOUSEEVENTF_ABSOLUTE,
                                 int(protocol.x * 65535), int(protocol.y * 65535))
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


if __name__ == "__main__":
    print(CoreConstants.greeting)
    is_main_loop_running = True
    while is_main_loop_running:
        client = ActionMulticastClient()
        loop = asyncio.get_event_loop()

        try:
            loop.run_until_complete(client.main())
        except KeyboardInterrupt:
            loop.run_until_complete(client.stop())
            break
        except:
            print("КРИТИЧЕСКАЯ ОШИБКА")
            traceback.print_exc()
            print("Рестарт через 5 секунд...")
            time.sleep(5)
        finally:
            loop.close()
