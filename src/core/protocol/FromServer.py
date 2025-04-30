from abc import ABC

from src.core.protocol.BasePacket import BasePacket


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
