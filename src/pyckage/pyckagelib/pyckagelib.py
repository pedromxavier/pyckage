"""`pyckagelib.py` @ pyckage.pyckagelib
"""
import os
import re
import sys
import site
import json
import argparse
import configparser
from dataclasses import dataclass
from contextlib import contextmanager

from .template import FileTemplate


@contextmanager
def chdir(path: str):
    cwd_path: str = os.path.abspath(os.getcwd())
    try:
        os.chdir(path)
        yield path
    finally:
        os.chdir(cwd_path)


class Validate:
    """"""

    class Invalid(Exception):
        pass

    @classmethod
    def _regex(cls, regex: re.Pattern, s: str, field: str = "", null: bool = False):
        if s is None and null:
            return s
        elif type(s) is not str or regex.match(s) is None:
            raise cls.Invalid(f"Invalid {field}: {s}")
        else:
            return s