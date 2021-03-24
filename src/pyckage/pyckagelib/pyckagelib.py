"""`pyckagelib.py` @ pyckage.pyckagelib
"""
import re

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

__all__ = ['Validate']