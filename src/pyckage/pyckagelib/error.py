"""`error.py` @ pyckage.pyckagelib
"""


class PyckageError(Exception):
    pass


class PyckageExit(Exception):
    def __init__(self, code: int = 0, *args: tuple, **kwargs: dict):
        Exception.__init__(self, *args, **kwargs)
        self.code = code