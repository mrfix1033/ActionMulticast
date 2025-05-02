import typing
from abc import ABC

from src.core.protocol.BasePacket import BasePacket
from src.core.utils import StringUtils


class FromServerPacket(BasePacket, ABC):
    pass


class ClientsConsoleVisiblePacket(FromServerPacket):
    def __init__(self, is_visible):
        self.is_visible = is_visible

    @staticmethod
    def get_id() -> str:
        return __class__.__name__

    def serialize(self) -> bytes:
        return str(int(self.is_visible)).encode()

    @staticmethod
    def deserialize(data: bytes):
        return ClientsConsoleVisiblePacket(bool(int(data.decode())))


class UpdateClientPacket(FromServerPacket):
    def __init__(self, file_bytes: bytes):
        self.file_bytes = file_bytes

    @staticmethod
    def get_id() -> str:
        return __class__.__name__

    def serialize(self) -> bytes:
        return self.file_bytes

    @staticmethod
    def deserialize(data: bytes):
        return UpdateClientPacket(data)


class StartupPacket(FromServerPacket):
    def __init__(self, is_add):
        self.is_add = is_add

    @staticmethod
    def get_id() -> str:
        return __class__.__name__

    def serialize(self) -> bytes:
        return str(int(self.is_add)).encode()

    @staticmethod
    def deserialize(data: bytes):
        return StartupPacket(bool(int(data.decode())))


class IAmServerPacket(FromServerPacket):
    @staticmethod
    def get_id() -> str:
        return __class__.__name__

    def serialize(self) -> bytes:
        return StringUtils.to_str_and_join().encode()

    @staticmethod
    def deserialize(data: bytes):
        return IAmServerPacket()


class FindPacket(FromServerPacket):
    find_types_literal = typing.Literal["sound", "video", "all"]
    find_types = ["sound", "video", "all"]

    def __init__(self, find_type: find_types_literal, volume: float):
        self.find_type = find_type
        self.volume = volume

    @staticmethod
    def get_id() -> str:
        return __class__.__name__

    def serialize(self) -> bytes:
        return f"{FindPacket.find_types.index(self.find_type)} {self.volume}".encode()

    @staticmethod
    def deserialize(data: bytes):
        data = data.decode().split(' ')
        return FindPacket(FindPacket.find_types[int(data[0])], float(data[1]))  # noqa
