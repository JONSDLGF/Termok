magic_code = b"\x7FELF"
MOD_ID     = 1

def getcode(BIN:bytearray) -> list[int, int, list]:
    if BIN[:len(magic_code)]==magic_code:
        return 0, MOD_ID, []
    return -1

def load() -> list[list[int, int], int]:...