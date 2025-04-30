import asyncio
import os.path
import shutil
import socket
import subprocess
import threading
import time
import traceback

import win32api
import win32con
import win32gui

from src.core.protocol.FromClient import UpdateClientResultPacket
from src.core.protocol.FromServer import UpdateClientPacket, StartupPacket, ClientsConsoleVisiblePacket

import src.core.utils.CommandsListener
from src.client import config
from src.client.commands import *
from src.core.CoreCommands import *
from src.core.Exceptions import LastReleaseAlreadyInstalled
from src.core.Loging import Logger
from src.core.Updater import Updater
from src.core.protocol.Keyboard import *
from src.core.protocol.Mouse import *
from src.core.protocol.ServerBroadcast import IAmServer
from src.core.utils.PacketUtils import PacketBuilder


class ActionMulticastClient:
    def __init__(self):
        self.version = CoreConstants.version
        self.updater = Updater(self.version, True)
        self.packet_builder = PacketBuilder()
        self.loop = asyncio.new_event_loop()
        self.running = True

        self.threads = []
        self.udp_client = None
        self.client = None

        self.console_hidden = False
        self.keyboard_listener = None
        self.console_window = win32gui.GetForegroundWindow()

    def main(self):
        if config.start_hidden:
            self.hide_console()

        self.threads = [
            threading.Thread(target=self.start_handle_input)
        ]
        for thread in self.threads:
            thread.start()

        self.keyboard_listener = self.run_keyboard_listener()

        self.loop.run_until_complete(self._async_start())  # blocking

    async def _async_start(self):
        await self.start_client()

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
            "startup": StartupCommand(),
            "check_update": CheckUpdate(self.updater.check_update),
            "update": UpdateCommand(self.update),
            "restart": RestartCommand(self.restart),
            "stop": StopCommand(self.stop),
            "version": Version(self.version),
        }
        commands_map["help"] = HelpCommand(list(commands_map.values()))
        src.core.utils.CommandsListener.start_listen_commands(commands_map, lambda: self.running)
        Logger.log("Обработка команд прекращена")

    def stop_logic(self):
        self.running = False
        global is_main_loop_running
        is_main_loop_running = False
        self.keyboard_listener.stop()
        if self.udp_client is not None:
            self.udp_client.close()
        if self.client is not None:
            self.client.close()
        self.loop.stop()

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

    async def start_client(self):
        while self.running:
            server_ip_port = config.server_ip, config.server_port
            if server_ip_port[0] is None:
                Logger.log("Поиск серверов...")
                server_ip_port = self.find_server()
            if server_ip_port is None:
                continue
            Logger.log(f"Подключение к {server_ip_port[0]}:{server_ip_port[1]}")
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.client:
                    try:
                        self.client.connect(server_ip_port)
                    except InterruptedError:
                        continue
                    Logger.log("Подключено")
                    self.start_listen_server()
            except ConnectionRefusedError:
                Logger.log("Соединение отклонено, повторное подключение через 5 секунд")
                time.sleep(5)
            except:
                Logger.error(traceback.format_exc())
            finally:
                Logger.log("Соединение закрыто")

    def find_server(self) -> typing.Optional[str]:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as self.udp_client:
            self.udp_client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.udp_client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.udp_client.bind(('0.0.0.0', config.beacon_port))

            packet_builder_udp = PacketBuilder()

            while self.running:
                Logger.log("Ожидание маяка...")
                # try:
                data, ip_port = self.udp_client.recvfrom(1024)
                # except OSError:
                #     continue                                      
                packet_builder_udp.put(data)
                while True:
                    bytes_excess = packet_builder_udp.get()
                    if bytes_excess is not None:
                        if packet_builder_udp.packet_name == IAmServer.get_id():
                            return ip_port
                        packet_builder_udp = PacketBuilder(bytes_excess)
                    else:
                        break
        return None

    def start_listen_server(self):
        while self.running:
            try:
                data = self.client.recv(1024)
            except ConnectionError:
                Logger.log("Соединение потеряно")
                break
            if not data:
                return
            self.packet_builder.put(data)
            while True:
                bytes_excess = self.packet_builder.get()
                if bytes_excess is not None:
                    packet_name, buffer = self.packet_builder.packet_name, self.packet_builder.buffer
                    self.packet_builder = PacketBuilder(
                        bytes_excess)  # если команда выдаст ошибку, она будет всё равно удалена из пакетбилдера
                    self.handle_command(packet_name, buffer)
                else:
                    break

    def handle_command(self, packet_name, packet_data):
        if packet_name == KeyboardPressPacket.get_id():
            packet = KeyboardPressPacket.deserialize(packet_data)
            win32api.keybd_event(packet.c, 0, 0, 0)
        elif packet_name == KeyboardReleasePacket.get_id():
            packet = KeyboardReleasePacket.deserialize(packet_data)
            win32api.keybd_event(packet.c, 0, win32con.KEYEVENTF_KEYUP, 0)
        elif packet_name == MouseMovementAbsolutePercentagePacket.get_id():
            packet = MouseMovementAbsolutePercentagePacket.deserialize(packet_data)
            win32api.mouse_event(win32con.MOUSEEVENTF_MOVE | win32con.MOUSEEVENTF_ABSOLUTE,
                                 int(packet.x * 65535), int(packet.y * 65535))
        elif packet_name == MousePressPacket.get_id():
            packet = MousePressPacket.deserialize(packet_data)
            if packet.b == 1:
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
            elif packet.b == 2:
                win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEDOWN, 0, 0)
            elif packet.b == 3:
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0)
            else:
                Logger.log("unknown mouse button pressed")
        elif packet_name == MouseReleasePacket.get_id():
            packet = MouseReleasePacket.deserialize(packet_data)
            if packet.b == 1:
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
            elif packet.b == 2:
                win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEUP, 0, 0)
            elif packet.b == 3:
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0)
            else:
                Logger.log("unknown mouse button pressed")
        elif packet_name == ClientsConsoleVisiblePacket.get_id():
            packet = ClientsConsoleVisiblePacket.deserialize(packet_data)
            if packet.is_visible:
                self.show_console()
            else:
                self.hide_console()
        elif packet_name == MouseScrollPacket.get_id():
            packet = MouseScrollPacket.deserialize(packet_data)
            win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, packet.dx, packet.dy)
        elif packet_name == UpdateClientPacket.get_id():
            Logger.log("Обновление с сервера...")
            successful = False
            try:
                temp_file_path = os.path.join(os.getenv("TEMP"), f"{CoreConstants.program_name}-update-from-server.exe")
                with open(temp_file_path, 'wb') as file:
                    file.write(packet_data)
                path_for_old = sys.executable + ".old"
                if os.path.exists(path_for_old):
                    os.remove(path_for_old)
                shutil.move(sys.executable, path_for_old)
                shutil.move(temp_file_path, sys.executable)
                successful = True
            finally:
                self.send_to_server(UpdateClientResultPacket(successful))
            Logger.log("Обновление установлено. Оно будет применено после перезапуска")
        elif packet_name == StartupPacket.get_id():
            packet = StartupPacket.deserialize(packet_data)
            if packet.is_add:
                Logger.log("По инициативе сервера, программа добавляется в автозагрузку...")
                StartupUtils.add_to_startup("Client")
                Logger.log("Программа добавлена в автозагрузку")
            else:
                Logger.log("По инициативе сервера, программа удаляется из автозагрузки...")
                StartupUtils.remove_from_startup("Client")
                Logger.log("Программа удалена из автозагрузки")
        else:
            Logger.log("unknown packet packet_name {}".format(packet_name))

    def send_to_server(self, packet: BasePacket):
        packet_bytes = packet.serialize()
        packet_data = f"{packet.get_id()} {len(packet_bytes)} ".encode() + packet_bytes
        self.client.send(packet_data)

    def run_keyboard_listener(self):
        from pynput import keyboard
        def on_activate():
            if self.console_hidden:
                self.show_console()
            else:
                self.hide_console()

        def get_func(hotkey_func):
            def func(key):
                if isinstance(key, keyboard.Key):
                    key = key.value
                key = key.vk
                hotkey_func(key)

            return func

        hotkey = keyboard.HotKey(config.keycodes_to_hide_show_console, on_activate)
        listener = keyboard.Listener(on_press=get_func(hotkey.press), on_release=get_func(hotkey.release))
        listener.start()
        return listener

    def hide_console(self):
        self.console_hidden = True
        win32gui.ShowWindow(self.console_window, win32con.SW_HIDE)
        Logger.log("Консоль скрыта")

    def show_console(self):
        self.console_hidden = False
        win32gui.ShowWindow(self.console_window, win32con.SW_SHOW)
        Logger.log("Консоль открыта")


if __name__ == "__main__":
    CoreConstants.init()
    Logger.log(CoreConstants.greeting("Client"))
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
            Logger.error("КРИТИЧЕСКАЯ ОШИБКА, пожалуйста, напишите автору")
            Logger.error(traceback.format_exc())
            Logger.log("Рестарт через 5 секунд...")
            time.sleep(5)
    Logger.log("Выполнение программы завершено")
