class ParseError(Exception):
    def __init__(self, msg: str = "") -> None:
        msg = "hq: parse error" + ": " if len(msg) else "" + msg
        super().__init__(msg)
