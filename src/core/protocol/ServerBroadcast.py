from src.core.protocol.Action import Action
from src.core.utils import StringUtils


class IAmServer(Action):
    @staticmethod
    def get_id() -> str:
        return __class__.__name__

    def serialize(self) -> bytes:
        return StringUtils.to_str_and_join(self.get_id()).encode()

    @staticmethod
    def deserialize(data: list[str]):
        return IAmServer()
