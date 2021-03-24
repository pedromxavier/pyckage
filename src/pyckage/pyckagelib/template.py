"""template.py @ pyckage.pyckagelib

This utility allows for file template generation, applying changes from a given dictionary.
"""
import pathlib

from .data import PackageData
from .tracker import FileTracker


class FileFormatter(dict):
    """"""

    def __getitem__(self, key):
        value = dict.__getitem__(self, key)
        return f"{{{key}}}" if value is None else value

    def __missing__(self, key):
        return f"{{{key}}}"


class FileTemplate:
    """"""

    FILE = "FILE"

    __hooks__ = {}

    def __init__(self, tracker: FileTracker = None, package_data: str = None):
        self.tracker = None if (tracker is None) else tracker
        self.package_data = None if (package_data is None) else PackageData(package_data)

    @property
    def track(self) -> bool:
        return self.tracker is not None

    @classmethod
    def template(cls, key: str):
        """Registers new template hook. A template hook is a bound method with the following signature:

        hook(from_: str, *args: tuple, **kwargs: dict) -> str

        Every hook is recorded under a key. Calling a template's make function with the `template` keyword argument will use `template` as key for loading the hook. Just as said, using the `args` and `kwargs` keyword arguments will tell what to pass for the hook.

        hook's return is a string telling from which file to read the template, i.e., overrides `from_` normal behavior. Thus, a regular use case would be to create a new template file from the usual one and use it right away. This allows for advanced template building. You might want to make use of the `tempfile` module.

        Parameters
        ----------
        key: str
            hook registry key
        """

        def decor(callback):
            cls.__hooks__[key] = callback
            return callback

        return decor

    def __default_hook(
        self, from_: str, to_: str, *args: tuple, **kwargs: dict
    ) -> (str, str):
        """Default behavior is to look at the package data folder."""
        return (self.package_data.get_data_path(from_), to_)

    def make(
        self,
        from_: str,
        to_: str,
        *,
        info: dict = None,
        template: str = None,
        args: tuple = None,
        kwargs: dict = None,
    ):
        """"""
        return self.__apply(f"{from_}.t", to_, info=info, args=args, kwargs=kwargs)

    def copy(self, from_: str, to_: str, args: tuple = None, kwargs: dict = None):
        """"""
        return self.__apply(from_, to_, args=args, kwargs=kwargs)

    def __apply(
        self,
        from_: str,
        to_: str,
        info: dict = None,
        template: str = None,
        args: tuple = None,
        kwargs: dict = None,
    ):
        """"""
        if template in self.__hooks__:
            hook = self.__hooks__[template]
        else:
            hook = self.__default_hook

        ## Retrieve path information
        from_path, to_path = hook(from_, *args, **kwargs)

        ## Read template file
        with open(from_path, mode="r") as r_file:
            source = r_file.read()

        ## Create and track generated file
        if self.track: self.tracker.create(self.FILE, to_path)

        with open(to_path, "w") as w_file:
            if info is None:
                w_file.write(source)
            else:
                w_file.write(source.format_map(FileFormatter(info)))


__all__ = ["FileTemplate"]