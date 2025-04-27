import datetime

from src.core.utils import StringUtils


class Logger:
    @staticmethod
    def log(*args, sep=' '):
        datetime_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        string = f"[{datetime_str}]: " + StringUtils.to_str_and_join(*args, sep)
        print(string)