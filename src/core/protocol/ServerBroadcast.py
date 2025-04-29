from src.core.protocol.Packet import Packet
from src.core.utils import StringUtils


class IAmServer(Packet):
    @staticmethod
    def get_id() -> str:
        return __class__.__name__

    def serialize(self) -> bytes:
        return StringUtils.to_str_and_join().encode()

    @staticmethod
    def deserialize(data: bytes):
        return IAmServer()
