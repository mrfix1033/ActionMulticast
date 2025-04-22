import abc

from src.core import StringUtils
from src.core.protocol.Action import Action


class MouseAction(Action, abc.ABC):
    pass


class MouseMovementAbsolutePercentageAction(MouseAction):
    def __init__(self, x: float, y: float):
        super().__init__()
        self.x = x
        self.y = y

    @staticmethod
    def get_id() -> str:
        return __class__.__name__

    def serialize(self) -> bytes:
        st = StringUtils.to_str_and_join(self.get_id(), self.x, self.y)
        return st.encode()

    @staticmethod
    def deserialize(data: list[str]):
        return MouseMovementAbsolutePercentageAction(float(data[0]), float(data[1]))


class MousePressAction(MouseAction):
    def __init__(self, b: int):
        super().__init__()
        self.b = b

    @staticmethod
    def get_id() -> str:
        return __class__.__name__

    def serialize(self) -> bytes:
        return StringUtils.to_str_and_join(self.get_id(), self.b).encode()

    @staticmethod
    def deserialize(data: list[str]):
        return MousePressAction(int(data[0]))


class MouseReleaseAction(MouseAction):
    def __init__(self, b: int):
        super().__init__()
        self.b = b

    @staticmethod
    def get_id() -> str:
        return __class__.__name__

    def serialize(self) -> bytes:
        return StringUtils.to_str_and_join(self.get_id(), self.b).encode()

    @staticmethod
    def deserialize(data: list[str]):
        return MouseReleaseAction(int(data[0]))


class MouseScrollAction(MouseAction):
    def __init__(self, dx: int, dy: int):
        super().__init__()
        self.dx = dx
        self.dy = dy

    @staticmethod
    def get_id() -> str:
        return __class__.__name__

    def serialize(self) -> bytes:
        return StringUtils.to_str_and_join(self.get_id(), self.dx, self.dy).encode()

    @staticmethod
    def deserialize(data: list[str]):
        return MouseScrollAction(int(data[0]), int(data[1]))
