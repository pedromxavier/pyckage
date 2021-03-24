import os
import re
import sys
import site
import json
import pathlib
import argparse
import platform
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
    Validate,
)

__version__ = "0.1.1"

## To be used with the module
_PYCKAGE_DATA = PackageData("pyckage")


class PyckageValidate(Validate):
    """"""

    RE_FLAGS = re.UNICODE

    RE_AUTHOR = re.compile(r"[\S ]+", RE_FLAGS)
    RE_USER = re.compile(r"[a-zA-Z]+", RE_FLAGS)
    RE_EMAIL = re.compile(
        r"^(([^<>()[\]\.,;:\s@\"]+(\.[^<>()[\]\.,;:\s@\"]+)*)|(\".+\"))@(([^<>()[\]\.,;:\s@\"]+\.)+[^<>()[\]\.,;:\s@\"]{2,})$",
        RE_FLAGS,
    )
    RE_VERSION = re.compile(
        r"^(0|[1-9]\d*)(\.(0|[1-9]\d*))(\.(0|[1-9]\d*))?$", RE_FLAGS
    )
    RE_PACKAGE = re.compile(r"^[a-zA-Z][a-zA-Z\_\-]+$", RE_FLAGS)
    RE_DESCRIPTION = re.compile(r"[\S\s]*", RE_FLAGS | re.MULTILINE)

    @classmethod
    def description(cls, description: str, null: bool = False) -> str:
        return cls._regex(cls.RE_DESCRIPTION, description, "description", null=null)

    @classmethod
    def author(cls, author: str, null: bool = False) -> str:
        return cls._regex(cls.RE_AUTHOR, author, "author", null=null)

    @classmethod
    def user(cls, user: str, null: bool = False) -> str:
        return cls._regex(cls.RE_AUTHOR, user, "user", null=null)

    @classmethod
    def email(cls, email: str, null: bool = False) -> str:
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

    @classmethod
    def meta(cls, meta: dict, null: bool = False) -> dict:
        return meta


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

    package_data = PackageData("pyckage")

    def __init__(
        self,
        *,
        description: str = None,
        package: str = None,
        version: str = None,
        author: str = None,
        email: str = None,
        user: str = None,
        path: str = None,
        meta: dict = None,
        args: argparse.Namespace = None,
        **kwargs,
    ):
        self.description = description
        self.package = package
        self.version = version
        self.author = author
        self.email = email
        self.args = args
        self.user = user
        self.path = path if path is None else pathlib.Path(path).absolute()
        self.meta = meta if meta is not None else {}

        self._py_min = self.kwget('py_min', self.meta, f'{sys.version_info.major}.{sys.version_info.minor}')
        self._py_max = self.kwget('py_max', self.meta, f'{sys.version_info.major + 1}')

        self.validate()
        # self.Tree = PyckageTree.Tree(package=self.package, args=self.args)
        # self.tree = self.Tree.tree()

    @classmethod
    def kwget(cls, key: object, kwargs: dict, default: object = None):
        try:
            return kwargs[key]
        except KeyError:
            return default

    def validate(self):
        try:
            # description
            self.description = PyckageValidate.description(self.description)

            # package
            self.package = PyckageValidate.package(self.package)

            # version
            self.version = PyckageValidate.version(self.version)

            # author
            self.author = PyckageValidate.author(self.author)

            # email
            self.email = PyckageValidate.email(self.email)

            # user
            self.user = PyckageValidate.user(self.user)

            self.validate_meta()
        except PyckageValidate.Invalid as error:
            raise ValueError(*error.args)

    def validate_meta(self):
        """"""
        self.meta = PyckageValidate.meta(self.meta)

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
    def load(cls, pyckage_path: str):
        path = pathlib.Path(pyckage_path).joinpath(".pyckage").absolute()

        if not path.exists():
            raise FileNotFoundError(f"No Pyckage installed at `{pyckage_path}`.")

        with open(path, mode="r") as file:
            return cls.from_dict(json.load(file))

    @classmethod
    def from_dict(cls, mapping: dict):
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
            author = config["author"]

        email: str = args.email

        if email is None:
            email = config["email"]

        user: str = args.user

        if user is None:
            user = config["user"]

        description: str = args.description

        if description is None:
            description = "?"

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
        """
        {
            'meta': {
                    'pyckage_version': '0.0.0',
                    'platform': 'windows',
                    'py_min': '3.7',
                    'py_max': '4',
                },
            'package': 'pyckage',
            'version': '1.0.0',
            'author': 'Author Smith',
            'email': 'author@email.net',
            'user': 'author1998',
            'path': 'c:/users/author/pyckage/',
            'description': 'This is clearly a Python Package'
        }
        """
        return json.dumps(
            {
                "meta": {
                    "pyckage_version": __version__,
                    "system_platform": platform.system(),
                    "py_min": pyckage._py_min,
                    "py_max": pyckage._py_max,
                },
                "description": "This is clearly a Python Package",
                "package": pyckage.package,
                "version": pyckage.version,
                "author": pyckage.author,
                "email": pyckage.email,
                "user": pyckage.user,
                "path": pyckage.path,
            }
        )

    @classmethod
    def JSON_DECODE(cls, data: dict):
        return cls(**data)

    # Some Checks
    @classmethod
    def has_pyckage(cls, path: str) -> bool:
        return pathlib.Path(path).joinpath(".pyckage").exists()

    @classmethod
    def exit(cls, code: int = 0, msg: str = ""):
        raise PyckageExit(code, msg)
