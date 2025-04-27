import time
import traceback

from src.core.CoreCommands import BaseCommand
from src.core.utils.CommandsUtils import unknown_command


def start_listen_commands(commands_map: dict[str, BaseCommand], is_running_func):
    print("Вы можете вводить команды")
    while is_running_func():
        try:
            command = input().lower().split(' ')
            command, args = command[0], command[1:]
            handler = commands_map.get(command)
            if handler is None:
                unknown_command()
                continue
            try:
                handler.execute(args)
            except:
                print("Во время выполнения команды произошла ошибка, пожалуйста, напишите автору")
                traceback.print_exc()
        except UnicodeDecodeError:
            time.sleep(0.5)
        except:
            traceback.print_exc()
