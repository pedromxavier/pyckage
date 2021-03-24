"""`data.py` @ pyckage.pyckagelib

This module provides the basic interfaces for reading/writing files hosted at a pyckage dat folder.

Other modules are heavily dependant in this one, thus it must not have any dependencies besides the standard library.
"""
import _io
import os
import sys
import site
import json
import pathlib


class PackageData:
    """"""

    __ref__ = {}

    def __new__(cls, package: str):
        """"""
        if package not in cls.__ref__:
            cls.__ref__[package] = object.__new__(cls)
        return cls.__ref__[package]

    def __init__(self, package: str):
        """"""
        self.package = package

    @property
    def package_data(self):
        return f"{self.package}_data"

    def get_config(self) -> dict:
        """"""
        with self.open_data(f".{self.package}-config", mode="r") as file:
            return json.load(file)

    def set_config(self, config: dict):
        """"""
        with self.open_data(f".{self.package}-config", mode="w") as file:
            json.dump(config, file)

    def get_data_path(self, fname: str) -> pathlib.Path:
        """

        Examples
        --------
        >>> PyckageData.get_data_path('') # retrieves base path
        """

        if self.package_data is not None:
            sys_path = (
                pathlib.Path(sys.prefix).joinpath(self.package_data, fname).absolute()
            )
            if not os.path.exists(sys_path):
                usr_path = (
                    pathlib.Path(site.USER_BASE)
                    .joinpath(self.package_data, fname)
                    .absolute()
                )
                if not os.path.exists(usr_path):
                    if fname:
                        raise FileNotFoundError(
                            f"File {fname} not installed in {self.package_data}."
                        )
                    else:
                        raise FileNotFoundError(
                            f"Package data `{self.package_data}` not installed."
                        )
                else:
                    return pathlib.Path(usr_path)
            else:
                return pathlib.Path(sys_path)
        else:
            raise NameError("PycakgeData.PACKAGE_DATA is not defined.")

    def open_data(
        self, fname: str, mode: str = "r", *args: tuple, **kwargs: dict
    ) -> _io.TextIOWrapper:
        """Opens file relative to package data folder.

        Parameters
        ----------
        fname: str
            File to open.
        mode: str
            File read mode, e.g., 'r', 'w', 'rb', 'wb', etc.
        *args: tuple
            Extra arguments for passing to open(...)
        **kwargs: dict
            Extra keyword-arguments for passing to open(...)
        """
        if self.package_data is None:
            raise NameError("PycakgeData.package_data is not defined.")
        else:
            path = self.get_data_path("")
            return open(
                path.joinpath(fname),
                mode=mode,
                *args,
                **kwargs,
            )

    def open_local(
        self, fname: str, *, path: str = None, mode: str = "r"
    ) -> _io.TextIOWrapper:
        """"""
        if path is None:
            return self.open_data(fname, mode=mode)
        else:
            path = pathlib.Path(path)
            return open(path.joinpath(fname), mode=mode)


__all__ = ["PackageData"]