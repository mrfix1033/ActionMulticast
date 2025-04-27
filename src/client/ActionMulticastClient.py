import asyncio
import os
import socket
import subprocess
import threading
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
        self.loop = asyncio.new_event_loop()
        self.running = True
        self.threads = []
        self.udp_client = None
        self.client = None

    def main(self):
        self.threads = [
            threading.Thread(target=self.start_handle_input),
            threading.Thread(target=self.updater.check_update),
        ]
        for thread in self.threads:
            thread.start()
        self.loop.run_until_complete(self._async_start())

    async def _async_start(self):
        await self.start_client()

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
            'restart': RestartCommand(self.restart),
            'stop': StopCommand(self.stop),
            'version': Version(self.version),
        }
        commands_map["help"] = HelpCommand(list(commands_map.values()))
        src.core.utils.CommandsListener.start_listen_commands(commands_map, lambda: self.running)
        print("Обработка команд прекращена")

    def stop_logic(self):
        self.running = False
        global is_main_loop_running
        is_main_loop_running = False
        if self.udp_client is not None:
            self.udp_client.close()
        if self.client is not None:
            self.client.close()
        self.loop.stop()

    def stop(self):
        print("Завершение работы...")
        self.stop_logic()
        print("Ожидание завершения работы...")

    def restart(self):
        print("Перезапуск...")
        self.stop_logic()

        client_or_server = "client"
        need_asset = f"ActionMulticast-{client_or_server}-{sys.platform}{CoreConstants.platform_to_extension[sys.platform]}"
        save_path = os.path.join(os.getenv('TEMP'), need_asset)

        bat_content = f"""
@echo off
chcp 65001
timeout /t 1 /nobreak
taskkill /IM "{os.path.basename(sys.executable)}" /F
timeout /t 1 /nobreak
move /Y "{save_path}" "{sys.executable}"
start "" "{sys.executable}"
del "%~f0"
    """
        bat_path = os.path.join(os.getenv('TEMP'), f"update_{os.getpid()}.bat")

        try:
            # 4. Гарантированная запись батника
            with open(bat_path, 'w', encoding='utf-8') as f:
                f.write(bat_content)
                f.flush()
                os.fsync(f.fileno())

            # 5. Запуск батника
            CREATE_NO_WINDOW = 0x08000000
            subprocess.Popen(
                ['cmd.exe', '/C', bat_path],
                creationflags=CREATE_NO_WINDOW,
                shell=True
            )

        except Exception as e:
            print(f"Критическая ошибка: {e}")
            traceback.print_exc()
        finally:
            os._exit(0)

    async def start_client(self):
        while self.running:
            server_ip_port = config.server_ip, config.server_port
            if server_ip_port[0] is None:
                print("Поиск серверов...")
                server_ip_port = self.find_server()
            if server_ip_port is None:
                continue
            print(f"Подключение к {server_ip_port[0]}:{server_ip_port[1]}")
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.client:
                    try:
                        self.client.connect(server_ip_port)
                    except InterruptedError:
                        continue
                    print("Подключено")
                    self.start_listen_server(self.client)
            except ConnectionRefusedError:
                print("Connection refused, waiting for 5 seconds")
                time.sleep(5)
            except:
                traceback.print_exc()
        print("Соединение закрыто")

    def find_server(self) -> typing.Optional[str]:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as self.udp_client:
            self.udp_client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.udp_client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.udp_client.bind(('0.0.0.0', config.beacon_port))

            command_buffer = PacketBuffer()

            while self.running:
                print("Ожидание маяка...")
                try:
                    data, ip_port = self.udp_client.recvfrom(1024)
                except OSError:
                    continue
                command_buffer.put(data.decode())
                commands = command_buffer.get()
                for command in commands:
                    command = command.split(' ')
                    if command[0] == IAmServer.get_id():
                        return ip_port
        return None

    def start_listen_server(self, client):
        while self.running:
            try:
                data = client.recv(1024)
            except OSError:
                continue
            except ConnectionResetError:
                print("Connection reset")
                break
            self.commands_buffer.put(data.decode())
            for command in self.commands_buffer.get():
                self.handle_command(command)

    def handle_command(self, text):
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
    print(CoreConstants.greeting("Client"))
    is_main_loop_running = True
    while is_main_loop_running:
        client = ActionMulticastClient()
        try:
            client.main()
            client.join()
        except KeyboardInterrupt:
            client.stop()
            client.join()
            break
        except:
            print("КРИТИЧЕСКАЯ ОШИБКА, пожалуйста, напишите автору")
            traceback.print_exc()
            print("Рестарт через 5 секунд...")
            time.sleep(5)
