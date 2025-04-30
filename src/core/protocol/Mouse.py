import abc

from src.core.utils import StringUtils
from src.core.protocol.BasePacket import BasePacket


class MousePacket(BasePacket, abc.ABC):
    pass


class MouseMovementAbsolutePercentagePacket(MousePacket):
    def __init__(self, x: float, y: float):
        super().__init__()
        self.x = x
        self.y = y

    @staticmethod
    def get_id() -> str:
        return __class__.__name__

    def serialize(self) -> bytes:
        st = StringUtils.to_str_and_join(self.x, self.y)
        return st.encode()

    @staticmethod
    def deserialize(data: bytes):
        data = data.decode().split(' ')
        return MouseMovementAbsolutePercentagePacket(float(data[0]), float(data[1]))


class MousePressPacket(MousePacket):
    def __init__(self, b: int):
        super().__init__()
        self.b = b

    @staticmethod
    def get_id() -> str:
        return __class__.__name__

    def serialize(self) -> bytes:
        return StringUtils.to_str_and_join(self.b).encode()

    @staticmethod
    def deserialize(data: bytes):
        data = data.decode().split(' ')
        return MousePressPacket(int(data[0]))


class MouseReleasePacket(MousePacket):
    def __init__(self, b: int):
        super().__init__()
        self.b = b

    @staticmethod
    def get_id() -> str:
        return __class__.__name__

    def serialize(self) -> bytes:
        return StringUtils.to_str_and_join(self.b).encode()

    @staticmethod
    def deserialize(data: bytes):
        data = data.decode().split(' ')
        return MouseReleasePacket(int(data[0]))


class MouseScrollPacket(MousePacket):
    def __init__(self, dx: int, dy: int):
        super().__init__()
        self.dx = dx
        self.dy = dy

    @staticmethod
    def get_id() -> str:
        return __class__.__name__

    def serialize(self) -> bytes:
        return StringUtils.to_str_and_join(self.dx, self.dy).encode()

    @staticmethod
    def deserialize(data: bytes):
        data = data.decode().split(' ')
        return MouseScrollPacket(int(data[0]), int(data[1]))
