import sys
import traceback
import typing
import winreg

from src.core import CoreConstants
from src.core.Loging import Logger


def add_to_startup(server_or_client: typing.Literal["Server", "Client"]):
    key_app_name = CoreConstants.program_name + server_or_client
    exe_path = sys.executable if getattr(sys, "frozen", False) else sys.argv[0]
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                key_path,
                0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.SetValueEx(key, key_app_name, 0, winreg.REG_SZ, f'"{exe_path}"')
    except:
        Logger.error("Ошибка при добавлении программы в автозагрузку")
        Logger.error(traceback.format_exc())

def remove_from_startup(server_or_client: str):
    key_app_name = CoreConstants.program_name + server_or_client
    try:
        with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.DeleteValue(key, key_app_name)
    except: pass