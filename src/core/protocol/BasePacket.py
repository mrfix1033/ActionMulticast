import abc


class BasePacket:
    @staticmethod
    @abc.abstractmethod
    def get_id() -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    def serialize(self) -> bytes:
        pass

    @staticmethod
    @abc.abstractmethod
    def deserialize(data: bytes):
        pass