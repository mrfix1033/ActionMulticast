import abc

from src.core.utils import StringUtils
from src.core.protocol.Packet import Packet


class KeyboardPacket(Packet, abc.ABC):
    pass


class KeyboardPressPacket(KeyboardPacket):
    def __init__(self, c: int):
        super().__init__()
        self.c = c

    @staticmethod
    def get_id() -> str:
        return __class__.__name__

    def serialize(self) -> bytes:
        return StringUtils.to_str_and_join(self.c).encode()

    @staticmethod
    def deserialize(data: bytes):
        data = data.decode().split(' ')
        return KeyboardPressPacket(int(data[0]))


class KeyboardReleasePacket(KeyboardPacket):
    def __init__(self, c: int):
        super().__init__()
        self.c = c

    @staticmethod
    def get_id() -> str:
        return __class__.__name__

    def serialize(self) -> bytes:
        return StringUtils.to_str_and_join(self.c).encode()

    @staticmethod
    def deserialize(data: bytes):
        data = data.decode().split(' ')
        return KeyboardReleasePacket(int(data[0]))
