import socket


def to_str_and_join(*args, delimiter=' ') -> str:
    return delimiter.join([str(arg) for arg in args])

def is_correct_ip(ip: str) -> bool:
    try:
        socket.inet_aton(ip)
    except:
        return False
    return True