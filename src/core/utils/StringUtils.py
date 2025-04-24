def to_str_and_join(*args, delimiter=' ') -> str:
    return delimiter.join([str(arg) for arg in args])