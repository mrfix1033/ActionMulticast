import asyncio
import traceback

import aioconsole

from src.core.CoreCommands import BaseCommand
from src.core.utils.CommandsUtils import unknown_command


async def start_listen_commands(commands_map: dict[str, BaseCommand], is_running_func):
    print("Вы можете вводить команды")
    while is_running_func():
        try:
            command = (await aioconsole.ainput()).lower().split(' ')
            command, args = command[0], command[1:]
            handler = commands_map.get(command)
            if handler is None:
                unknown_command()
                continue
            try:
                await handler.execute(args)
            except:
                print("Во время выполнения команды произошла ошибка, пожалуйста, напишите мне")
                traceback.print_exc()
        except (KeyboardInterrupt, EOFError, asyncio.CancelledError):
            pass
        except:
            traceback.print_exc()
