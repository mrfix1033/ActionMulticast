from abc import ABC

from src.core.protocol.BasePacket import BasePacket


class FromClientPacket(BasePacket, ABC):
    pass


class UpdateClientResultPacket(FromClientPacket):
    def __init__(self, is_successful):
        self.is_successful = is_successful

    @staticmethod
    def get_id() -> str:
        return __class__.__name__

    def serialize(self) -> bytes:
        return str(int(self.is_successful)).encode()

    @staticmethod
    def deserialize(data: bytes):
        return UpdateClientResultPacket(bool(int(data.decode())))
