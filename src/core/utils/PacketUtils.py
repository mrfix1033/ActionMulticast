class PacketBuffer:
    def __init__(self):
        self.buffer = ""

    def put(self, data: str):
        self.buffer += data

    def get(self) -> list[str]:
        return_index = self.buffer.rfind('\n')
        commands, self.buffer = (self.buffer[:return_index],
                                 self.buffer[return_index + 1:])
        return commands.split("\n")
