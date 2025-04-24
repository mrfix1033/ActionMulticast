import abc

from src.core.utils import StringUtils
from src.core.protocol.Action import Action


class KeyboardAction(Action, abc.ABC):
    pass


class KeyboardPressAction(KeyboardAction):
    def __init__(self, c: int):
        super().__init__()
        self.c = c

    @staticmethod
    def get_id() -> str:
        return __class__.__name__

    def serialize(self) -> bytes:
        return StringUtils.to_str_and_join(self.get_id(), self.c).encode()

    @staticmethod
    def deserialize(data: list[str]):
        return KeyboardPressAction(int(data[0]))


class KeyboardReleaseAction(KeyboardAction):
    def __init__(self, c: int):
        super().__init__()
        self.c = c

    @staticmethod
    def get_id() -> str:
        return __class__.__name__

    def serialize(self) -> bytes:
        return StringUtils.to_str_and_join(self.get_id(), self.c).encode()

    @staticmethod
    def deserialize(data: list[str]):
        return KeyboardReleaseAction(int(data[0]))
