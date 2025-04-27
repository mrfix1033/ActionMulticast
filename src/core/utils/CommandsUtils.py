from src.core.Loging import Logger


def not_enough_arguments(usage):
    Logger.log(f"Недостаточно аргументов\n{usage}")


def incorrect_usage(usage):
    Logger.log(f"Неверное использование\n{usage}")


def unknown_command():
    Logger.log("Неизвестная команда, используйте help для просмотра команд")
