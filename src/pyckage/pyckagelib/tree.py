"""tree.py @ pyckage.pyckagelib
"""
import os
import pathlib

from .data import PackageData
from .template import FileTemplate, FileTracker


class FileTree(object):

    DIR = "DIR"
    FILE = "FILE"

    FILE_TYPES = {FILE, DIR, None}

    package_data: PackageData

    __args__ = {}

    def __init__(
        self,
        type_: str,
        head: str = None,
        tail: list = None,
        *,
        cond: bool = True,
        template: FileTemplate = None,
    ):
        """"""
        self.type = type_
        self.head = head
        self.tail = tail
        self.cond = cond

        self.template = FileTemplate() if template is None else template

    def __call__(
        self,
        type_: str,
        head: str = None,
        tail: list = None,
        *,
        cond: bool = True,
        template: FileTemplate = None,
    ):
        return self.__class__(type_, head, tail, cond=cond, template=template)

    def __getitem__(self, key: str):
        return self.__args__[key]

    @classmethod
    def Tree(cls, **attrs: dict):
        """
        This allows for a dynamic type creation.
        """

        class _TreeType(cls):
            """"""

            __args__ = {**cls.__args__, **attrs}

        return _TreeType

    @classmethod
    def root(cls, tail: list, **kwargs):
        """"""
        return cls(None, None, tail, **kwargs)

    @classmethod
    def default_path(cls) -> pathlib.Path:
        return pathlib.Path(os.getcwd())

    def file_hook(self, path: pathlib.Path):
        """"""
        self.template.touch(path)

    def dir_hook(self, path: pathlib.Path):
        os.mkdir(path)

    def grow(self, root_path: pathlib.Path):
        if self.type is not None:
            if not self.cond:
                return

            path = root_path.joinpath(self.head)

            if self.type == self.FILE:
                self.file_hook(path)
                return
            elif self.type == self.DIR:
                self.dir_hook(path)
            else:
                raise NameError(f"Invalid path type {self.type}")

        for subtree in self.tail:
            subtree.grow(path)