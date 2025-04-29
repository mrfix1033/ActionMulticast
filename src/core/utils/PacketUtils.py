import typing

"""
Информация о пакете (название, длина данных) становится известна по мере поступления данных.
Сначала идёт поиск имени, потом поиск длины пакета, потом принимаются данные, пока весь буфер не будет заполнен.
Для заполнения буфера - put(), для обработки и получения остаточных данных - get().
Если буфер ещё не заполнен (пакет не готов), get() возращает None.
Если пакет готов, get() возращает байты, которые принадлежат другому пакету. Может вернуть пустой массив байтов.
После того, как get() вернул не None, можно получить название пакета из packet_name и его данные из buffer.  
"""


class PacketBuilder:
    def __init__(self, buffer=bytes()):
        self.buffer = buffer
        self.packet_name = None
        self.packet_length = None

    def put(self, data: bytes):
        self.buffer += data

    def get(self) -> typing.Optional[bytes]:
        if self.packet_name is None:
            split = self.buffer.split(b' ', 1)
            if len(split) == 2:
                self.packet_name = split[0].decode()
                self.buffer = split[1]
        if self.packet_length is None:
            split = self.buffer.split(b' ', 1)
            if len(split) == 2:
                self.packet_length = int(split[0].decode())
                self.buffer = split[1]
        if self.packet_length is None or len(self.buffer) < self.packet_length:
            return None
        self.buffer, bytes_excess = self.buffer[:self.packet_length], self.buffer[self.packet_length:]
        return bytes_excess

    def __str__(self):
        return f"{__class__.__name__}({self.packet_name}, {self.packet_length}, {self.buffer})"