import os
import re
import sys
import site
import json
import pathlib
import argparse
import configparser
from contextlib import contextmanager
from dataclasses import dataclass

## Exceptions
from .pyckagelib.error import PyckageError, PyckageExit
from .pyckagelib import (
    PackageData,
    FileTree,
    FileTemplate,
    FileTracker,
    Config,
    Validate,
)

__version__ = "0.1.0"

## To be used with the module
_PYCKAGE_DATA = PackageData("pyckage")


@dataclass
class PyckageConfig(Config):
    author: str
    email: str
    user: str


class PyckageValidate(Validate):
    """"""

    RE_AUTHOR = None
    RE_EMAIL = re.compile(
        r"^(([^<>()[\]\.,;:\s@\"]+(\.[^<>()[\]\.,;:\s@\"]+)*)|(\".+\"))@(([^<>()[\]\.,;:\s@\"]+\.)+[^<>()[\]\.,;:\s@\"]{2,})$"
    )
    RE_VERSION = re.compile(r"^(0|[1-9]\d*)(\.(0|[1-9]\d*))(\.(0|[1-9]\d*))?$")
    RE_PACKAGE = re.compile(r"^[a-zA-Z][a-zA-Z\_\-]+$")

    @classmethod
    def author(cls, author: str, null: bool = False):
        return author

    @classmethod
    def user(cls, user: str, null: bool = False):
        return user

    @classmethod
    def email(cls, email: str, null: bool = False):
        return cls._regex(cls.RE_EMAIL, email, "email", null=null)

    @classmethod
    def version(cls, version: str, null: bool = False) -> str:
        return cls._regex(cls.RE_VERSION, version, "version", null=null)

    @classmethod
    def package(cls, package: str, null: bool = False) -> str:
        return cls._regex(cls.RE_PACKAGE, package, "package name", null=null)

    @classmethod
    def path(cls, path: {str, None}, null: bool = False) -> str:
        if path is None:
            return os.path.abspath(os.getcwd())
        elif type(path) is str:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Path `{path}` not found.")
            else:
                return os.path.abspath(path)
        else:
            raise TypeError(f"Invalid path type {type(path)}")


class PyckageTemplate(FileTemplate):
    """"""

    package_data = _PYCKAGE_DATA

    @FileTemplate.template("setup.cfg")
    def setupcfg(
        self, from_: str, namespace: argparse.Namespace, *args: tuple, **kwargs: dict
    ) -> str:
        cfg_files = ["setup-plain.cfg.t"]

        if namespace.data:
            cfg_files.append("setup-data.cfg.t")

        if namespace.script:
            cfg_files.append("setup-script.cfg.t")

        if namespace.github:
            cfg_files.append("setup-github.cfg.t")

        ## Parse all configuration templates.
        parser = configparser.ConfigParser()
        parser.read([self.package_data.get_data_path(fname) for fname in cfg_files])

        ## Summarise and write to file.
        with self.package_data.open_data("setup.cfg.t", mode="w") as file:
            parser.write(file)

        return "setup.cfg"


class PyckageTree(FileTree):
    def tree(self):
        return self.root(
            [
                self(
                    self.DIR,
                    "src",
                    [
                        self(
                            self.DIR,
                            self["package"],
                            [
                                self(self.FILE, "__init__.py", template="__init__.py"),
                                self(
                                    self.DIR,
                                    f"{self['package']}lib",
                                    [
                                        self(
                                            self.FILE,
                                            "__init__.py",
                                            template="packagedata.__init__.py",
                                        ),
                                        self(
                                            self.FILE,
                                            f"{self['package']}lib.py",
                                            template="packagelib.py",
                                        ),
                                    ],
                                    cond=self["args"].data,
                                ),
                            ],
                        ),
                    ],
                ),
                self(
                    self.DIR,
                    "bin",
                    [self(self.FILE, self["package"], template="package")],
                    cond=self["args"].script,
                ),
                self(self.DIR, "docs", []),
                self(self.DIR, "data", [], cond=self["args"].data),
                self(self.FILE, "setup.py", template="setup.py"),
                self(self.FILE, "setup.cfg"),
            ]
        )


class Pyckage(object):
    """"""

    package_data = PackageData("pyckage", config_type=PyckageConfig)

    def __init__(
        self,
        *,
        package: str = None,
        version: str = None,
        author: str = None,
        email: str = None,
        user: str = None,
        path: str = None,
        args: argparse.Namespace = None,
        description: str = None,
        **kwargs,
    ):
        self.description = description
        self.package = package
        self.version = version
        self.author = author
        self.email = email
        self.args = args
        self.user = user
        self.path = pathlib.Path(path).absolute()

        # self.Tree = PyckageTree.Tree(package=self.package, args=self.args)
        # self.tree = self.Tree.tree()

    @property
    def json(self):
        return {
            "description": self.description,
            "package": self.package,
            "author": self.author,
            "path": self.path,
        }

    @property
    def config(self):
        return self.package_data.get_config()

    @property
    def version(self):
        return {
            # Package Version
            "version": __version__,
            # Python Version
            "PY_MIN": f"{sys.version_info.major}.{sys.version_info.minor}",  # Inclusive
            "PY_MAX": f"{sys.version_info.major + 1}",  # Exclusive
        }

    @property
    def info(self):
        return {**self.json, **self.config, **self.version}

    @classmethod
    def load(cls, args: argparse.Namespace):
        path = pathlib.Path(PyckageValidate.path(args.path))

        pyckage_path = path.joinpath(".pyckage")

        if os.path.exists(pyckage_path):
            with open(pyckage_path, mode="r") as file:
                return cls.from_json(json.load(file))
        else:
            cls.exit(1, f"No pyckage defined at `{path}`.")

    @classmethod
    def from_json(cls, mapping: dict):
        return cls(**mapping)

    @classmethod
    def from_args(cls, args: argparse.Namespace):
        """"""
        ## Get pyckage path
        path = pathlib.Path(args.path).absolute()

        if not path.exists():
            raise FileNotFoundError(f"No target directory `{path}`.")
        elif not path.is_dir():
            raise OSError(f"`{path}` is not a directory.")

        pyckage_path = path.joinpath(".pyckage")

        if pyckage_path.exists():
            raise FileExistsError(
                "There is an existing Pyckage in this folder. Try running `pyckage update` or `pyckage fix`"
            )

        package: str = args.package

        if package is None:
            package = path.stem

        version: str = args.version

        if version is None:
            version = "0.0.0"

        config = cls.package_data.get_config()

        author: str = args.author

        if author is None:
            author = config['author']

        email: str = args.email

        if email is None:
            email = config['email']

        user: str = args.user

        if user is None:
            user = config['user']

        description: str = args.description

        if description is None:
            description = '?'

        pyckage = cls(
            package=package,
            version=version,
            author=author,
            email=email,
            user=user,
            path=path,
            args=args,
            description=description,
        )

        return pyckage

    @classmethod
    def JSON_ENCODE(cls, pyckage):
        return {}

    @classmethod
    def JSON_DECODE(cls, ):
        return cls()

    @classmethod
    def exit(cls, code: int = 0, msg: str = ""):
        raise PyckageExit(code, msg)
