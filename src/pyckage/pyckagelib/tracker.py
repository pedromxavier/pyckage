import os
import sys


class FileTracker:
    """"""

    DIR = "DIR"
    FILE = "FILE"

    FILE_TYPES = {DIR, FILE}

    def __init__(self, pathlog: list = None):
        self.pathlog = list(pathlog) if pathlog is not None else []

    @staticmethod
    def touch(path: str):
        """"""
        with open(path, "a"):
            pass

    def clear(self):
        """"""
        while self.pathlog:
            type_, path = self.pathlog.pop()
            try:
                if type_ == self.FILE:
                    os.remove(path)
                    print(f"Remove FILE `{path}`.")
                elif type_ == self.DIR:
                    os.rmdir(path)
                    print(f"Remove DIR `{path}`.")
                else:
                    raise TypeError
            except:
                raise EnvironmentError(
                    "Fatal Error: run `pyckage fix` or try fixing package contents manually."
                )

    def create(self, type_: str, path: str):
        """"""
        if os.path.exists(path):
            raise FileExistsError(f"`{path}` already exists.")
        elif type_ in self.FILE_TYPES:
            if type_ == self.DIR:
                os.mkdir(path)
                self.pathlog.append((type_, path))
                print(f"Create FILE `{path}`.")
            elif type_ == self.FILE:
                self.touch(path)
                self.pathlog.append((type_, path))
                print(f"Create DIR `{path}`.")
            else:
                raise TypeError(f"Invalid type {type_}.")
        else:
            raise TypeError(f"Invalid type {type_}.")
